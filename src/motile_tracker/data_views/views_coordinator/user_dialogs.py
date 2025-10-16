from qtpy.QtCore import Qt
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QMessageBox


def confirm_force_operation(message: str) -> bool:
    """Ask user if they want to force the operation by breaking conflicting edges."""

    msg = QMessageBox()
    msg.setWindowTitle("Force operation?")
    msg.setTextFormat(Qt.PlainText)

    message += "\n\nDo you want to force this operation by breaking conflicting edges?"
    msg.setText(message)
    msg.setIconPixmap(QIcon.fromTheme("dialog-question").pixmap(64, 64))

    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msg.setDefaultButton(QMessageBox.No)

    result = msg.exec_()
    return result == QMessageBox.Yes
