import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QCheckBox
from PyQt5.QtCore import QTimer, Qt, QRect
from mss import mss

from selection_overlay import SelectionOverlay
from pip_window import PipWindow

class ScreenCaptureApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("화면 영역 PIP 도구")
        self.setGeometry(100, 100, 400, 200)
        
        # 메인 위젯 설정
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 레이아웃 설정
        self.layout = QVBoxLayout(self.central_widget)
        
        # 상태 레이블
        self.status_label = QLabel("시작하려면 '영역 선택' 버튼을 클릭하세요.")
        self.layout.addWidget(self.status_label)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        
        # 영역 선택 버튼
        self.select_area_btn = QPushButton("영역 선택")
        self.select_area_btn.clicked.connect(self.select_area)
        button_layout.addWidget(self.select_area_btn)
        
        # 자동 업데이트 체크박스
        self.auto_update_check = QCheckBox("자동 업데이트")
        self.auto_update_check.setChecked(True)
        button_layout.addWidget(self.auto_update_check)
        
        # 레이아웃에 버튼 레이아웃 추가
        self.layout.addLayout(button_layout)
        
        # 캡처 영역 정보 초기화
        self.capture_area = None
        self.capture_img = None
        self.pip_window = None
        
        # 스크린 캡처 라이브러리 초기화 및 모니터 정보 가져오기
        self.sct = mss()
        self.monitor_info = self.sct.monitors[0]  # 전체 화면 사용
        
        # 자동 업데이트 타이머
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_capture)
    
    def select_area(self):
        self.hide()  # 메인 윈도우 숨기기
        
        QTimer.singleShot(500, self.start_area_selection)
    
    def start_area_selection(self):
        # 투명한 오버레이로 영역 선택
        self.overlay = SelectionOverlay(self.monitor_info)
        self.overlay.set_callback(self.on_area_selected)
        self.overlay.show()
    
    def on_area_selected(self, rect):
        # 선택한 영역의 좌표 가져오기
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        
        # 영역이 충분히 큰지 확인
        if w > 250 and h > 100:
            # 캡처 영역 저장 (시스템 좌표계 사용)
            self.capture_area = (x, y, w, h)
            
            # 디버그 정보 출력
            print(f"선택한 영역: x={x}, y={y}, w={w}, h={h}")
            
            try:
                # 선택한 영역 캡처
                with mss() as sct:
                    # 캡처 영역 설정 (절대 좌표 사용)
                    monitor = {"left": x, "top": y, "width": w, "height": h}
                    # 영역 캡처
                    sct_img = sct.grab(monitor)
                    
                    # 이미지를 numpy 배열로 변환
                    screen_np = np.array(sct_img)
                    # BGRA에서 RGB로 변환
                    self.capture_img = cv2.cvtColor(screen_np, cv2.COLOR_BGRA2RGB)
                
                # PIP 창 생성
                if self.pip_window:
                    self.pip_window.close()
                
                self.pip_window = PipWindow(self.capture_img)
                self.pip_window.show()
                
                # 자동 업데이트 시작
                if self.auto_update_check.isChecked():
                    self.update_timer.start(16)  # 16ms 간격으로 업데이트
                
                self.status_label.setText(f"선택한 영역: ({x}, {y}, {w}, {h})")
            except Exception as e:
                self.status_label.setText(f"오류 발생: {str(e)}")
                print(f"캡처 오류: {str(e)}")
        else:
            self.status_label.setText("선택한 영역이 너무 작습니다.")
        
        self.show()  # 메인 윈도우 다시 표시
    
    def update_capture(self):
        if self.capture_area and self.pip_window and self.auto_update_check.isChecked():
            x, y, w, h = self.capture_area
            
            try:
                # 화면 캡처 (MSS 사용)
                with mss() as sct:
                    # 캡처 영역 설정 (절대 좌표 사용)
                    monitor = {"left": x, "top": y, "width": w, "height": h}
                    # 영역 캡처
                    sct_img = sct.grab(monitor)
                    
                    # 이미지를 numpy 배열로 변환
                    screen_np = np.array(sct_img)
                    # BGRA에서 RGB로 변환
                    screen_rgb = cv2.cvtColor(screen_np, cv2.COLOR_BGRA2RGB)
                
                # PIP 창 업데이트
                self.pip_window.update_image(screen_rgb)
            except Exception as e:
                print(f"업데이트 오류: {str(e)}")
                # 오류 발생 시 타이머 중지
                self.update_timer.stop()
                self.status_label.setText(f"업데이트 오류: {str(e)}")
    
    def closeEvent(self, event):
        if self.pip_window:
            self.pip_window.close()
        
        if self.update_timer.isActive():
            self.update_timer.stop()
        
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScreenCaptureApp()
    window.show()
    sys.exit(app.exec_())
