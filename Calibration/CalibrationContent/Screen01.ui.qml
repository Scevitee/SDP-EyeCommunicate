

/*
This is a UI file (.ui.qml) that is intended to be edited in Qt Design Studio only.
It is supposed to be strictly declarative and only uses a subset of QML. If you edit
this file manually, you might introduce QML code that is not supported by Qt Design Studio.
Check out https://doc.qt.io/qtcreator/creator-quick-ui-forms.html for details on .ui.qml files.
*/
import QtQuick 2.15
import QtQuick.Controls 2.15
import Calibration 1.0

Rectangle {
    id: rectangle
    width: Constants.width
    height: Constants.height

    color: Constants.backgroundColor

    Image {
        id: image1
        width: 100
        height: 100
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.leftMargin: 0
        anchors.topMargin: 0
        source: "../../src/SDP-EyeCommunicate/eyetracking/assets/Circular-Point-icon.png"
        fillMode: Image.PreserveAspectFit
    }

    Image {
        id: image2
        width: 100
        height: 100
        anchors.top: parent.top
        anchors.topMargin: 0
        source: "../../src/SDP-EyeCommunicate/eyetracking/assets/Circular-Point-icon.png"
        anchors.horizontalCenter: parent.horizontalCenter
        fillMode: Image.PreserveAspectFit
    }

    Image {
        id: image3
        x: 1820
        width: 100
        height: 100
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.rightMargin: 0
        anchors.topMargin: 0
        source: "../../src/SDP-EyeCommunicate/eyetracking/assets/Circular-Point-icon.png"
        fillMode: Image.PreserveAspectFit
    }

    Image {
        id: image4
        width: 100
        height: 100
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: parent.left
        anchors.leftMargin: 0
        source: "../../src/SDP-EyeCommunicate/eyetracking/assets/Circular-Point-icon.png"
        fillMode: Image.PreserveAspectFit
    }

    Image {
        id: image5
        width: 100
        height: 100
        anchors.verticalCenter: parent.verticalCenter
        source: "../../src/SDP-EyeCommunicate/eyetracking/assets/Circular-Point-icon.png"
        anchors.horizontalCenter: parent.horizontalCenter
        fillMode: Image.PreserveAspectFit
    }

    Image {
        id: image6
        x: 1820
        width: 100
        height: 100
        anchors.verticalCenter: parent.verticalCenter
        anchors.right: parent.right
        anchors.rightMargin: 0
        source: "../../src/SDP-EyeCommunicate/eyetracking/assets/Circular-Point-icon.png"
        anchors.verticalCenterOffset: 0
        fillMode: Image.PreserveAspectFit
    }

    Image {
        id: image7
        y: 980
        width: 100
        height: 100
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        anchors.leftMargin: 0
        anchors.bottomMargin: 0
        source: "../../src/SDP-EyeCommunicate/eyetracking/assets/Circular-Point-icon.png"
        fillMode: Image.PreserveAspectFit
    }

    Image {
        id: image8
        y: 980
        width: 100
        height: 100
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 0
        source: "../../src/SDP-EyeCommunicate/eyetracking/assets/Circular-Point-icon.png"
        anchors.horizontalCenter: parent.horizontalCenter
        fillMode: Image.PreserveAspectFit
    }
    states: [
        State {
            name: "clicked"
        }
    ]
    Image {
        id: image9
        x: 1820
        y: 980
        width: 100
        height: 100
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.rightMargin: 0
        anchors.bottomMargin: 0
        source: "../../src/SDP-EyeCommunicate/eyetracking/assets/Circular-Point-icon.png"
        fillMode: Image.PreserveAspectFit
    }
}
