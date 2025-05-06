from PyQt5.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QSlider
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QCursor

class PipWindow(QMainWindow):
    def __init__(self, img, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.img = img
        self.opacity = 1.0
        
        # 원본 이미지 크기와 비율 저장
        self.original_height, self.original_width = img.shape[:2]
        self.aspect_ratio = self.original_width / self.original_height
        
        # 메인 위젯 설정
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 레이아웃 설정
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)  # 여백 제거
        self.layout.setSpacing(0)  # 위젯 간 간격 제거
        
        # 이미지 레이블
        self.img_label = QLabel()
        self.img_label.setScaledContents(True)  # 이미지가 라벨 크기에 맞게 스케일링되도록 설정
        self.update_image(img)
        self.layout.addWidget(self.img_label)
        
        # 컨트롤 패널을 위한 위젯
        self.control_widget = QWidget()
        self.control_widget.setFixedHeight(40)  # 컨트롤 패널 높이 고정
        self.control_widget.setStyleSheet("background-color: rgba(60, 60, 60, 255);")  # 배경색 추가
        
        control_layout = QHBoxLayout(self.control_widget)
        control_layout.setContentsMargins(5, 5, 5, 5)  # 컨트롤 패널 내부 여백 설정
        
        # 투명도 슬라이더
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.setFixedWidth(150)  # 버튼 너비 고정
        self.opacity_slider.valueChanged.connect(self.change_opacity)
        
        # 닫기 버튼
        self.close_btn = QPushButton("닫기")
        self.close_btn.setFixedWidth(50)  # 버튼 너비 고정
        self.close_btn.setStyleSheet("background-color: rgba(200,200,200,100);")  # 배경색 추가
        self.close_btn.clicked.connect(self.close)
        
        # 레이아웃에 위젯 추가
        opacity_label = QLabel("투명도:")
        opacity_label.setStyleSheet("color: white;")  # 텍스트 색상 설정
        control_layout.addWidget(opacity_label)
        control_layout.addWidget(self.opacity_slider, 1)  # 슬라이더에 stretch 1 부여
        control_layout.addStretch() 
        control_layout.addWidget(self.close_btn)
        
        self.layout.addWidget(self.control_widget)
        
        # 드래그를 위한 변수
        self.dragging = False
        self.resizing = False
        self.resize_edge = None
        self.offset = None
        
        # 테두리 설정 - 더 넓게 설정하여 사용성 개선
        self.border_width = 10  # 테두리 두께 증가 (더 쉽게 잡을 수 있도록)
        self.visible_border_width = 2  # 실제 보이는 테두리 두께
        self.border_color = QColor(255, 255, 255)  # 흰색 테두리
        
        # 리사이즈를 위한 마우스 추적 활성화
        self.setMouseTracking(True)
        self.central_widget.setMouseTracking(True)  # 중앙 위젯에도 마우스 추적 활성화
        self.img_label.setMouseTracking(True)       # 이미지 라벨에도 마우스 추적 활성화
        
        # 초기 크기 설정 (컨트롤 패널 높이 고려)
        control_height = self.control_widget.height()
        self.resize(self.original_width, self.original_height + control_height)

    
    def update_image(self, img):
        h, w, c = img.shape
        qimg = QImage(img.data, w, h, w * c, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        self.img_label.setPixmap(pixmap)
    
    def change_opacity(self, value):
        self.opacity = value / 100
        self.setWindowOpacity(self.opacity)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            cursor_pos = event.pos()
            
            # 테두리 영역인지 확인 (리사이징용)
            edge = self.get_edge_at(cursor_pos)
            if edge:
                self.resizing = True
                self.resize_edge = edge
                self.setCursor(self.get_resize_cursor(edge))
            else:
                # 이미지 영역인지 확인 (드래그용)
                img_height = self.height() - self.control_widget.height()
                if cursor_pos.y() <= img_height:  # 이미지 영역 내에서만 드래그 가능
                    self.dragging = True
                    self.offset = event.pos()
    
    def mouseMoveEvent(self, event):
        pos = event.pos()
        
        # 컨트롤 패널 위치 확인
        control_height = self.control_widget.height()
        img_height = self.height() - control_height
        
        # 컨트롤 패널 영역에서는 항상 일반 커서 사용
        if pos.y() >= img_height:
            if self.cursor().shape() != Qt.ArrowCursor:
                self.setCursor(Qt.ArrowCursor)
            return  # 컨트롤 패널에서는 추가 처리 없이 종료
        
        if self.resizing and self.resize_edge:
            # 리사이징 처리
            self.do_resize(pos)
        elif self.dragging and self.offset:
            # 드래그 처리
            self.move(self.pos() + pos - self.offset)
        else:
            # 커서 모양 변경을 위한 처리 (테두리 위에 있을 때)
            edge = self.get_edge_at(pos)
            if edge:
                cursor = self.get_resize_cursor(edge)
                if self.cursor().shape() != cursor:
                    self.setCursor(cursor)
            elif self.cursor().shape() != Qt.ArrowCursor:
                self.setCursor(Qt.ArrowCursor)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.resizing = False
            self.resize_edge = None
            self.setCursor(Qt.ArrowCursor)
    
    def get_edge_at(self, pos):
        # 경계에서 테두리 너비 이내인지 확인 (픽셀 단위)
        margin = self.border_width
        width = self.width()
        height = self.height()
        
        # 컨트롤 패널 위치 확인
        control_height = self.control_widget.height()
        img_height = height - control_height
        
        # 컨트롤 패널 영역에서는 항상 None 반환 (리사이징 비활성화)
        if pos.y() >= img_height:
            return None
        
        # 테두리 영역 검사를 더 관대하게 설정 (사용성 개선)
        if pos.x() <= margin:  # 왼쪽 경계
            if pos.y() <= margin:
                return "top-left"
            elif pos.y() >= img_height - margin:
                return "bottom-left"
            else:
                return "left"
        elif pos.x() >= width - margin:  # 오른쪽 경계
            if pos.y() <= margin:
                return "top-right"
            elif pos.y() >= img_height - margin:
                return "bottom-right"
            else:
                return "right"
        elif pos.y() <= margin:  # 위쪽 경계
            return "top"
        elif pos.y() >= img_height - margin:  # 아래쪽 경계 (컨트롤 패널 위쪽)
            return "bottom"
        
        return None
    
    def get_resize_cursor(self, edge):
        # 각 모서리와 경계에 대한 커서 설정
        if edge in ["left", "right"]:
            return Qt.SizeHorCursor
        elif edge in ["top", "bottom"]:
            return Qt.SizeVerCursor
        elif edge in ["top-left", "bottom-right"]:
            return Qt.SizeFDiagCursor
        elif edge in ["top-right", "bottom-left"]:
            return Qt.SizeBDiagCursor
        return Qt.ArrowCursor
    
    def do_resize(self, pos):
        # 현재 창 정보
        current_pos = self.pos()
        current_size = self.size()
        
        # 컨트롤 패널의 높이 (고정값)
        control_height = self.control_widget.height()
        
        # 새 크기와 위치 계산
        new_pos_x = current_pos.x()
        new_pos_y = current_pos.y()
        new_width = current_size.width()
        new_height = current_size.height()
        
        # 현재 이미지 영역 높이 (컨트롤 패널 제외)
        img_height = new_height - control_height
        
        # 각 방향별 리사이징 처리
        if "left" in self.resize_edge:
            # 왼쪽 경계 이동
            width_change = current_pos.x() + current_size.width() - (pos.x() + current_pos.x())
            height_change = width_change / self.aspect_ratio
            
            new_pos_x = pos.x()
            new_width = width_change
            new_height = height_change + control_height  # 컨트롤 패널 높이 추가
            
        if "right" in self.resize_edge:
            # 오른쪽 경계 이동
            width_change = pos.x()
            height_change = width_change / self.aspect_ratio
            
            new_width = width_change
            new_height = height_change + control_height  # 컨트롤 패널 높이 추가
            
        if "top" in self.resize_edge:
            # 위쪽 경계 이동
            height_change = current_pos.y() + img_height - (pos.y() + current_pos.y())
            width_change = height_change * self.aspect_ratio
            
            new_pos_y = pos.y()
            new_width = width_change
            new_height = height_change + control_height  # 컨트롤 패널 높이 추가
            
        if "bottom" in self.resize_edge:
            # 아래쪽 경계 이동 (컨트롤 패널 위치 고려)
            height_change = pos.y() - current_pos.y()
            width_change = height_change * self.aspect_ratio
            
            new_width = width_change
            new_height = height_change + control_height  # 컨트롤 패널 높이 추가
        
        # 최소 크기 제한
        min_width = 100
        min_img_height = min_width / self.aspect_ratio
        min_height = min_img_height + control_height
        
        if new_width < min_width:
            new_width = min_width
            new_height = min_img_height + control_height
        
        # 위치와 크기 업데이트
        if "left" in self.resize_edge or "top" in self.resize_edge:
            # 왼쪽이나 위쪽 경계를 조정할 때만 위치 변경
            if "left" in self.resize_edge:
                new_pos_x = current_pos.x() + current_size.width() - new_width
            if "top" in self.resize_edge:
                new_pos_y = current_pos.y() + img_height - (new_height - control_height)
            
            self.move(new_pos_x, new_pos_y)
        
        # 크기 업데이트
        self.resize(int(new_width), int(new_height))
    
    def paintEvent(self, event):
        # 테두리 그리기
        painter = QPainter(self)
        painter.setOpacity(self.opacity)
        
        # 안티앨리어싱 설정
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 이미지 영역 계산
        img_height = self.height() - self.control_widget.height()
        
        # 테두리 펜 설정 - 시각적으로 보이는 테두리는 얇게 유지
        pen = QPen(self.border_color)
        pen.setWidth(self.visible_border_width)
        painter.setPen(pen)
        
        # 이미지 영역 주변에 테두리 그리기 (실제 테두리는 얇게)
        painter.drawRect(
            self.visible_border_width // 2,  # 테두리 위치 조정
            self.visible_border_width // 2, 
            self.width() - self.visible_border_width,  # 테두리 두께 고려
            img_height - self.visible_border_width
        )
        
        # 테두리 부분이 리사이징 영역임을 나타내기 위한 시각적 표시
        # 마우스 위치에 따라 해당 테두리를 강조할 수도 있음
        current_edge = self.get_edge_at(self.mapFromGlobal(QCursor.pos()))
        if current_edge:
            highlight_pen = QPen(QColor(100, 200, 255))  # 파란색으로 강조
            highlight_pen.setWidth(self.visible_border_width * 2)
            painter.setPen(highlight_pen)
            
            # 현재 마우스가 있는 테두리 부분 강조
            if "left" in current_edge:
                painter.drawLine(
                    self.visible_border_width // 2,
                    0, 
                    self.visible_border_width // 2,
                    img_height
                )
            if "right" in current_edge:
                painter.drawLine(
                    self.width() - self.visible_border_width // 2,
                    0, 
                    self.width() - self.visible_border_width // 2,
                    img_height
                )
            if "top" in current_edge:
                painter.drawLine(
                    0,
                    self.visible_border_width // 2, 
                    self.width(),
                    self.visible_border_width // 2
                )
            if "bottom" in current_edge:
                painter.drawLine(
                    0,
                    img_height - self.visible_border_width // 2, 
                    self.width(),
                    img_height - self.visible_border_width // 2
                )
        
        # 이미지와 컨트롤 패널 사이에 구분선 그리기
        painter.setPen(QPen(self.border_color, 1))
        painter.drawLine(0, img_height, self.width(), img_height)