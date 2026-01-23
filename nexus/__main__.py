"""Allow running nexus as a module: python -m nexus"""
from nexus.ui.cli import main
import sys

if __name__ == "__main__":
    # Check for launcher command
    if len(sys.argv) > 1 and sys.argv[1] == "launcher":
        from nexus.launcher import main as launcher_main
        sys.exit(launcher_main() or 0)
    
    sys.exit(main())
