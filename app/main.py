"""Entry point for kong-verter desktop application."""

import customtkinter as ctk

from app.ui.app import KonverterApp


def main() -> None:
    """Launch the Kong-verter GUI."""
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = KonverterApp()
    app.mainloop()


if __name__ == "__main__":
    main()
