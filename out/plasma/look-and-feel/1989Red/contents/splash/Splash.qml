import QtQuick 2.15

Rectangle {
    id: root
    color: "#181821"
    property int stage

    Image {
        anchors.fill: parent
        source: "images/splash.jpg"
        fillMode: Image.PreserveAspectFit
        smooth: true
    }
}
