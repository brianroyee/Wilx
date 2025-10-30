import os

def start_shell():
    cwd = os.getcwd()

    while True:
        try:
            user_input = input(f"{cwd} $ ").strip()

            if not user_input:
                continue

            if user_input in ("exit", "quit"):
                break

            print(f"[DEBUG] You entered: {user_input}")

        except KeyboardInterrupt:
            print("\n(Use 'exit' to quit)")
            continue
        except EOFError:
            # handle Ctrl+Z / EOF
            break
