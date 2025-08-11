!define PRODUCT_NAME "Edge LLM Base"
!define PRODUCT_VERSION "1.0"
!define PRODUCT_PUBLISHER "YourName"

SetCompressor lzma

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "setup.exe"
InstallDir "$PROGRAMFILES\EdgeLLMBase"
ShowInstDetails show

Section "MainSection" SEC01
  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer
  File "dist\edge_llm_base.exe"  ; PyInstaller输出
  File "qwen3-0.6b-q4.gguf"     ; 打包模型
  CreateDirectory "$SMPROGRAMS\Edge LLM Base"
  CreateShortCut "$SMPROGRAMS\Edge LLM Base\Edge LLM Base.lnk" "$INSTDIR\edge_llm_base.exe"
  CreateShortCut "$DESKTOP\Edge LLM Base.lnk" "$INSTDIR\edge_llm_base.exe"
SectionEnd

Section -Post
  WriteUninstaller "$INSTDIR\uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "UninstallString" "$INSTDIR\uninstall.exe"
SectionEnd

Section Uninstall
  Delete "$INSTDIR\edge_llm_base.exe"
  Delete "$INSTDIR\qwen3-0.6b-q4.gguf"
  Delete "$INSTDIR\uninstall.exe"
  Delete "$SMPROGRAMS\Edge LLM Base\Edge LLM Base.lnk"
  Delete "$DESKTOP\Edge LLM Base.lnk"
  RMDir "$SMPROGRAMS\Edge LLM Base"
  RMDir "$INSTDIR"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
SectionEnd