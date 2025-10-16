from qtpy.QtCore import Qt
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QMessageBox


def confirm_force_operation(message: str) -> tuple[bool, bool]:
    """
    Ask the user if they want to force the operation by breaking conflicting edges.

    Returns:
        (force_now, set_always)
        - force_now: True if user selected 'Yes' or 'Yes'
        - set_always: True if user selected 'Yes, always'
    """

    msg = QMessageBox()
    msg.setWindowTitle("Force operation?")
    msg.setTextFormat(Qt.PlainText)

    message += "\n\nDo you want to force this operation by breaking conflicting edges?"
    msg.setText(message)
    msg.setIconPixmap(QIcon.fromTheme("dialog-question").pixmap(64, 64))

    yes_button = msg.addButton("Yes", QMessageBox.YesRole)
    always_button = msg.addButton("Yes, always", QMessageBox.AcceptRole)
    msg.addButton("No", QMessageBox.NoRole)

    msg.setDefaultButton(yes_button)

    msg.exec_()
    clicked = msg.clickedButton()

    if clicked == yes_button:
        return True, False
    elif clicked == always_button:
        return True, True
    else:
        return False, False
