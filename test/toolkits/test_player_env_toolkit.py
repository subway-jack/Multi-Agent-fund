# tests/test_player_env_toolkit_cli_map.py
# ------------------------------------------------------------
# End-to-end test for PlayerEnvToolkit with user-provided files.
# Features:
#   - Accept host->sandbox file mappings:  --map "host_path:dest_rel" (repeatable)
#   - Optional custom player script:       --player-host /path/to/player.py
#   - Optional in-sandbox env path:        --env-in-sandbox src/environment.py
#   - Optional per-call pip reqs:          --requirements "pkg1,pkg2"
#   - Works even if you provide nothing: will create a tiny player + environment.
# ------------------------------------------------------------

import os
import sys
import argparse
import tempfile
from textwrap import dedent
from pprint import pprint

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

# Adjust this import if your module path differs
import src.toolkits.player_env_toolkit as pet_mod
from src.toolkits.sandbox_toolkit import SandboxToolkit
from src.models import BaseModelBackend
from src.models import ModelFactory
from src.types import ModelPlatformType,ModelType

single_model = ModelFactory.create(
    model_platform=ModelPlatformType.OPENAI,
    model_type=ModelType.GPT_4O_MINI,
    model_config_dict={"temperature": 0},
)

# -------------------------- helpers to synthesize files --------------------------

def ensure_host_llm_stub():
    """Ensure host-side utils/llm.py exists (PlayerEnvToolkit uploads it)."""
    llm_dir = os.path.join(PROJECT_ROOT, "utils")
    llm_path = os.path.join(llm_dir, "llm.py")
    if not os.path.exists(llm_path):
        os.makedirs(llm_dir, exist_ok=True)
        with open(llm_path, "w", encoding="utf-8") as f:
            f.write("def call_llm(*args, **kwargs):\n    return \"[]\"  # stub for tests\n")
    return llm_path


def make_temp_player_py(path: str) -> None:
    """Create a minimal player that honors --env-file/--env-class/--max-steps."""
    code = dedent(r"""
        import argparse, importlib.util, json

        def load_class(path, class_name):
            spec = importlib.util.spec_from_file_location("env_mod", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore
            return getattr(mod, class_name)

        def main():
            p = argparse.ArgumentParser()
            p.add_argument("--env-file", required=True)
            p.add_argument("--env-class", default="TextGame")
            p.add_argument("--max-steps", type=int, default=50)
            args = p.parse_args()

            TextGame = load_class(args.env_file, args.env_class)
            game = TextGame(0)

            if hasattr(game, "getTaskDescription"):
                try:
                    print("Task:", game.getTaskDescription())
                except Exception:
                    pass

            steps = 0
            over = False
            won = False
            score = 0.0
            obs = ""

            while steps < args.max_steps:
                acts = list(game.generatePossibleActions())
                act = acts[0] if acts else ""
                obs, score, reward, over, won = game.step(act)
                print(f"step={steps} action={act} score={score} over={over} won={won}")
                steps += 1
                if over:
                    break

            print(json.dumps({
                "done": bool(over),
                "game_won": bool(won),
                "score": float(score),
                "step": int(steps),
                "history": [],
                "actions": acts if acts else [],
                "obs_tail": obs[-200:] if isinstance(obs, str) else str(obs),
                "error": None
            }))
        if __name__ == "__main__":
            main()
    """)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)


def default_env_code() -> str:
    """A tiny environment that wins when action 'finish' is chosen."""
    return dedent(r"""
        class TextGame:
            def __init__(self, randomSeed=0):
                self.observationStr = "You are in a test room."
                self.numSteps = 0
                self.gameOver = False
                self.gameWon = False
                self.score = 0.0

            def getTaskDescription(self):
                return "Finish the game by choosing 'finish'."

            def generatePossibleActions(self):
                return ["finish", "look around"]

            def step(self, action):
                self.numSteps += 1
                if action == "finish":
                    self.gameOver = True
                    self.gameWon = True
                    self.score = 1.0
                    self.observationStr = "Game finished."
                elif action == "look around":
                    self.observationStr = "You look around. Nothing changes."
                else:
                    self.observationStr = "I don't understand that."
                return (self.observationStr, self.score, 0.0, self.gameOver, self.gameWon)
    """)


# -------------------------- CLI parsing --------------------------

def parse_kv_map(s: str) -> tuple[str, str]:
    """
    Parse "host_path:dest_rel" or "host_path=dest_rel".
    """
    if ":" in s:
        host, dest = s.split(":", 1)
    elif "=" in s:
        host, dest = s.split("=", 1)
    else:
        raise argparse.ArgumentTypeError(f"Invalid mapping '{s}'. Use 'host:dest' or 'host=dest'.")
    host = host.strip()
    dest = dest.strip()
    if not host or not dest:
        raise argparse.ArgumentTypeError(f"Invalid mapping '{s}'. Empty host or dest.")
    return host, dest


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Runtime test for PlayerEnvToolkit with user file mappings.")
    p.add_argument("--benchmark", choices=["cwmb", "bytesize32", "pddl"], default="bytesize32")
    p.add_argument("--player-host", type=str, default=None,
                   help="Host path to a player script. If omitted, a minimal temp player is used.")
    p.add_argument("--map", action="append", type=parse_kv_map, default=[],
                   help="Mapping 'host_path:dest_rel' into sandbox (repeatable).")
    p.add_argument("--env-in-sandbox", type=str, default="src/environment.py",
                   help="In-sandbox path to the environment file used by play_env.")
    p.add_argument("--step-limit", type=int, default=10)
    p.add_argument("--requirements", type=str, default="",
                   help="Comma-separated pip packages to install before run (optional).")
    p.add_argument("--workdir", type=str, default=None,
                   help="In-sandbox working directory to cd into before running.")
    p.add_argument("--no-assert", action="store_true", help="Skip asserts (for manual runs).")
    return p


# -------------------------- main --------------------------

def main():
    args = build_argparser().parse_args()

    # Ensure utils/llm.py exists on host unless user already mapped one
    mapped_llm = any(dest == "utils/llm.py" for _, dest in args.map)
    if not mapped_llm:
        ensure_host_llm_stub()

    # If user provided a custom player, patch BENCHMARK_FILE_PATH; else synthesize a temp one.
    if args.player_host:
        pet_mod.BENCHMARK_FILE_PATH[args.benchmark] = args.player_host
    else:
        tmp_dir = tempfile.mkdtemp(prefix="pet_player_")
        host_player_path = os.path.join(tmp_dir, "dummy_player.py")
        make_temp_player_py(host_player_path)
        pet_mod.BENCHMARK_FILE_PATH[args.benchmark] = host_player_path

    # Create sandbox toolkit with safe defaults
    sandbox = SandboxToolkit(
        default_file_map={},          # we control uploads explicitly below
        default_requirements=[],      # avoid network ops during tests by default
        bootstrap_on_init=False,
        memory_limit_mb=256,
        timeout_minutes=5,
    )

    # Instantiate PlayerEnvToolkit
    reqs = [x for x in (args.requirements.split(",") if args.requirements else []) if x.strip()]
    pet = pet_mod.PlayerEnvToolkit(
        benchmark_type=args.benchmark,
        sandbox_toolkit=sandbox,
        model=single_model,
        env_requirements=reqs,
        default_workdir=args.workdir,
    )

    # Import user-provided mappings (host -> sandbox)
    if args.map:
        user_map = {host: dest for host, dest in args.map}
        res = sandbox.import_file_map(user_map)
        print("\n=== import_file_map(user_map) ===")
        pprint(res)
        if not res.get("success", False):
            raise RuntimeError(f"File import failed: {res.get('error')}")

    # If the specified env file does not exist in the sandbox, write a default one
    check_res = sandbox.code_tool(
        action="run_bash",
        bash_cmd=f"test -f {args.env_in_sandbox} && echo EXIST || echo MISSING"
    )
    exists_flag = "EXIST" in (check_res.get("stdout") or "")
    if not exists_flag:
        print(f"\nEnvironment '{args.env_in_sandbox}' not found in sandbox; writing default env.")
        save_res = sandbox.file_tool("save", args.env_in_sandbox, default_env_code())
        assert save_res.get("success") is True, f"Failed to write default env: {save_res}"

    # Run the player
    result = pet.play_env(file_path=args.env_in_sandbox, step_limit=args.step_limit)

    print("\n=== PlayerEnvToolkit result ===")
    pprint(result)

    # Assertions (optional)
    if not args.no_assert:
        assert isinstance(result, dict)
        assert "play_result" in result and "result_analysis" in result
        play_res = result["play_result"]
        assert isinstance(play_res.get("success"), bool)
        assert "stdout" in play_res and "stderr" in play_res
        assert isinstance(result["result_analysis"], str)

        # If the default env is used, we expect success True
        if not exists_flag:
            assert play_res.get("success") is True, f"Sandbox run failed: {play_res}"

    print("\nAll PlayerEnvToolkit CLI mapping tests completed.")


if __name__ == "__main__":
    main()