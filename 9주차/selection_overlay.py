import sys
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPainter, QPen, QColor, QCursor

class SelectionOverlay(QWidget):
    def __init__(self, monitor_info, parent=None):
        super().__init__(parent)
        # 투명한 전체 화면 오버레이 설정
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 모니터 정보 저장
        self.monitor_info = monitor_info
        
        # 현재 화면의 전체 가상 화면 크기 설정
        screen_geo = QRect(
            self.monitor_info['left'],
            self.monitor_info['top'],
            self.monitor_info['width'],
            self.monitor_info['height']
        )
        self.setGeometry(screen_geo)
        
        # 영역 선택을 위한 변수
        self.start_point = None
        self.end_point = None
        self.selecting = False
        self.selected_rect = None
        
        # 화면을 어둡게 만들기 위한 오버레이 색상
        self.overlay_color = QColor(0, 0, 0, 100)  # 반투명 검은색
        self.border_color = QColor(255, 255, 255)  # 흰색 테두리
        
        # 선택 완료 시 호출될 콜백 함수
        self.selection_callback = None
        
        # 커서 설정
        self.setCursor(Qt.CrossCursor)
        
        # ESC 키로 취소할 수 있도록 키보드 포커스 설정
        self.setFocusPolicy(Qt.StrongFocus)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        
        # 전체 화면을 반투명한 오버레이로 덮기
        painter.fillRect(self.rect(), self.overlay_color)
        
        # 선택 영역이 있으면 그리기
        if self.selecting and self.start_point and self.end_point:
            # 선택 영역 계산
            selection_rect = self.calculate_rect(self.start_point, self.end_point)
            
            # 선택 영역은 투명하게
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(selection_rect, Qt.transparent)
            
            # 선택 영역 테두리 그리기
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.setPen(QPen(self.border_color, 2, Qt.SolidLine))
            painter.drawRect(selection_rect)
            
            # 선택 영역 정보 표시
            text = f"{selection_rect.width()} x {selection_rect.height()}"
            painter.setPen(Qt.white)
            painter.drawText(selection_rect.bottomRight() + QPoint(10, 10), text)
    
    def calculate_rect(self, start, end):
        return QRect(min(start.x(), end.x()), 
                    min(start.y(), end.y()),
                    abs(start.x() - end.x()),
                    abs(start.y() - end.y()))
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_point = event.pos()
            self.end_point = event.pos()
            self.selecting = True
            self.update()
    
    def mouseMoveEvent(self, event):
        if self.selecting:
            self.end_point = event.pos()
            self.update()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.selecting:
            self.end_point = event.pos()
            self.selecting = False
            self.selected_rect = self.calculate_rect(self.start_point, self.end_point)
            
            # 선택 영역이 유효하면 콜백 호출
            if self.selected_rect.width() > 10 and self.selected_rect.height() > 10:
                if self.selection_callback:
                    # 선택한 영역의 좌표를 시스템 좌표에 맞게 변환
                    adjusted_rect = QRect(
                        self.selected_rect.x() + self.monitor_info['left'],
                        self.selected_rect.y() + self.monitor_info['top'],
                        self.selected_rect.width(),
                        self.selected_rect.height()
                    )
                    self.selection_callback(adjusted_rect)
            
            self.close()
    
    def keyPressEvent(self, event):
        # ESC 키를 눌러 선택 취소
        if event.key() == Qt.Key_Escape:
            self.close()
    
    def set_callback(self, callback):
        self.selection_callback = callback