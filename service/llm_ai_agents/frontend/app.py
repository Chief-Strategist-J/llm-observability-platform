import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from frontend.pages.chat.state.state import ChatState
from frontend.pages.chat.controller.controller import ChatController
from frontend.pages.chat.ui.ui import ChatUI

def main():
    state = ChatState()
    controller = ChatController()
    ui = ChatUI(controller, state)

    ui.render_page_config()
    params = ui.render_sidebar()
    ui.render_header()
    ui.render_health_checks()
    ui.render_chat_history()
    ui.render_chat_input(params)
    ui.render_footer(params["model_config_path"])

if __name__ == "__main__":
    main()
