!include "MUI.nsh"
!include "FileAssociation.nsh"

!define APPNAME "chiahub.io monitor"
!define COMPANYNAME "cryptico GmbH"
!define DESCRIPTION "monitor and upload index of chia plots"
!define VERSIONMAJOR 0
!define VERSIONMINOR 0
!define VERSIONBUILD 3

!define HELPURL "https://github.com/yan74/chiahub-monitor" # "Support Information" link
!define UPDATEURL "https://github.com/yan74/chiahub-monitor" # "Product Updates" link
!define ABOUTURL "https://www.chiahub.io" # "Publisher" link

!define INSTALLSIZE 314065

Name "chiahub.io monitor"
Icon "${NSISDIR}\Contrib\Graphics\Icons\orange-install.ico"
OutFile "chiahub.io-monitor-installer_x86-64.exe"
InstallDir $PROGRAMFILES64\chiahub-monitor
InstallDirRegKey HKLM "Software\cryptico\chiahub-monitor" "Install_Dir"
RequestExecutionLevel admin
LicenseData "LICENSE"

!include LogicLib.nsh

page license
page directory
Page instfiles

!macro VerifyUserIsAdmin
UserInfo::GetAccountType
pop $0
${If} $0 != "admin" ;Require admin rights on NT4+
        messageBox mb_iconstop "Administrator rights required!"
        setErrorLevel 740 ;ERROR_ELEVATION_REQUIRED
        quit
${EndIf}
!macroend

function .onInit
    setShellVarContext all
    !insertmacro VerifyUserIsAdmin
functionEnd

UninstPage uninstConfirm
UninstPage instfiles

section "install"
  WriteRegStr HKLM Software\cryptico\chiahub-monitor "Install_Dir" "$INSTDIR"

  SetOutPath $INSTDIR
  File /r "dist\main\*.*"
  File "logo.ico"

  WriteUninstaller "$INSTDIR\uninstall.exe"

  createShortCut "$SMPROGRAMS\${APPNAME}.lnk" "$INSTDIR\chiahub-monitor.exe" "" "$INSTDIR\logo.ico"

  # Registry information for add/remove programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME} - ${DESCRIPTION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "QuietUninstallString" "$\"$INSTDIR\uninstall.exe$\" /S"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "InstallLocation" "$\"$INSTDIR$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayIcon" "$\"$INSTDIR\logo.ico$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "Publisher" "${COMPANYNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "HelpLink" "$\"${HELPURL}$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLUpdateInfo" "$\"${UPDATEURL}$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLInfoAbout" "$\"${ABOUTURL}$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayVersion" "$\"${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}$\""
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "VersionMajor" ${VERSIONMAJOR}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "VersionMinor" ${VERSIONMINOR}
    # There is no option for modifying or repairing the install
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoRepair" 1
    # Set the INSTALLSIZE constant (!defined at the top of this script) so Add/Remove Programs can accurately report the size
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "EstimatedSize" ${INSTALLSIZE}

SectionEnd

;--------------------------------

; Uninstaller

function un.onInit
    SetShellVarContext all

    !insertmacro VerifyUserIsAdmin
functionEnd

UninstallText "This will uninstall chiahub.io-monitor. Hit next to continue."
UninstallIcon "${NSISDIR}\Contrib\Graphics\Icons\orange-uninstall.ico"

Section "uninstall"

  # Remove Start Menu launcher
  delete "$SMPROGRAMS\${APPNAME}.lnk"

  DeleteRegKey HKLM "Software\cryptico\chiahub-monitor"

  Delete "logo.ico"
  Delete "$INSTDIR\uninstall.exe"

  RMDir /r "$INSTDIR"

  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"

  IfFileExists "$INSTDIR" 0 NoErrorMsg
    MessageBox MB_OK "Note: $INSTDIR could not be removed!" IDOK 0 ; skipped if file doesn't exist
  NoErrorMsg:

SectionEnd
