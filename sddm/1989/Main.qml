import QtQuick 2.15
import QtQuick.Controls 2.15
import SddmComponents 2.0

Rectangle {
    id: root
    width: 1920
    height: 1080
    color: "#181821"
    Text {
        anchors.centerIn: parent
        anchors.verticalCenterOffset: -80
        text: "1989"
        color: "#cdd6f4"
        font.family: "Hack"
        font.pixelSize: 72
    }
    Column {
        anchors.centerIn: parent
        anchors.verticalCenterOffset: 40
        spacing: 12
        width: 280
        TextField {
            id: name
            width: parent.width
            text: userModel.lastUser
            color: "#bdc5e3"
            font.family: "Hack"
        }
        TextField {
            id: pw
            width: parent.width
            echoMode: TextInput.Password
            color: "#bdc5e3"
            font.family: "Hack"
            onAccepted: sddm.login(name.text, pw.text, session.index)
        }
        Button {
            text: "Log in"
            font.family: "Hack"
            onClicked: sddm.login(name.text, pw.text, session.index)
        }
    }
    ComboBox {
        id: session
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        anchors.margins: 24
        model: sessionModel
        textRole: "name"
        font.family: "Hack"
    }
}
