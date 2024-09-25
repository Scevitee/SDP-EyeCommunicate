

/*
This is a UI file (.ui.qml) that is intended to be edited in Qt Design Studio only.
It is supposed to be strictly declarative and only uses a subset of QML. If you edit
this file manually, you might introduce QML code that is not supported by Qt Design Studio.
Check out https://doc.qt.io/qtcreator/creator-quick-ui-forms.html for details on .ui.qml files.
*/
import QtQuick 6.5
import QtQuick.Controls 6.5
import Designtest
import QtQuick.Studio.DesignEffects

Rectangle {
    id: rectangle
    width: Constants.width
    height: Constants.height

    color: Constants.backgroundColor

    AnimatedImage {
        id: animatedImage
        width: 100
        height: 100
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.leftMargin: 0
        anchors.topMargin: 0
        source: "../../../SDP-EyeCommunicate/eyetracking/assets/Circular-Point-icon.png"
        property int orderid: 0
    }

    AnimatedImage {
        id: animatedImage1
        x: 910
        y: 0
        width: 100
        height: 100
        anchors.top: parent.top
        anchors.topMargin: 0
        source: "../../../SDP-EyeCommunicate/eyetracking/assets/Circular-Point-icon.png"
        property int orderid: 1
        anchors.horizontalCenter: parent.horizontalCenter
    }

    AnimatedImage {
        id: animatedImage2
        x: 1820
        y: 0
        width: 100
        height: 100
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.rightMargin: 0
        anchors.topMargin: 0
        source: "../../../SDP-EyeCommunicate/eyetracking/assets/Circular-Point-icon.png"
        property int orderid: 0
    }

    AnimatedImage {
        id: animatedImage3
        x: 0
        y: 490
        width: 100
        height: 100
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: parent.left
        anchors.leftMargin: 0
        source: "../../../SDP-EyeCommunicate/eyetracking/assets/Circular-Point-icon.png"
    }

    AnimatedImage {
        id: animatedImage4
        x: 910
        y: 490
        width: 100
        height: 100
        anchors.verticalCenter: parent.verticalCenter
        source: "../../../SDP-EyeCommunicate/eyetracking/assets/Circular-Point-icon.png"
        anchors.horizontalCenter: parent.horizontalCenter
    }

    AnimatedImage {
        id: animatedImage5
        x: 1820
        y: 490
        width: 100
        height: 100
        anchors.verticalCenter: parent.verticalCenter
        anchors.right: parent.right
        anchors.rightMargin: 0
        source: "../../../SDP-EyeCommunicate/eyetracking/assets/Circular-Point-icon.png"
    }

    AnimatedImage {
        id: animatedImage6
        x: 0
        y: 980
        width: 100
        height: 100
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        anchors.leftMargin: 0
        anchors.bottomMargin: 0
        source: "../../../SDP-EyeCommunicate/eyetracking/assets/Circular-Point-icon.png"
    }

    AnimatedImage {
        id: animatedImage7
        x: 910
        y: 980
        width: 100
        height: 100
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 0
        source: "../../../SDP-EyeCommunicate/eyetracking/assets/Circular-Point-icon.png"
        anchors.horizontalCenter: parent.horizontalCenter
    }

    AnimatedImage {
        id: animatedImage8
        x: 1820
        y: 980
        width: 100
        height: 100
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.rightMargin: 0
        anchors.bottomMargin: 0
        source: "../../../SDP-EyeCommunicate/eyetracking/assets/Circular-Point-icon.png"
    }
}
