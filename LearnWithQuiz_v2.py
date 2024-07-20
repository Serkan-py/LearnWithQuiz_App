import sys
import os
import json
import random
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QMessageBox, QRadioButton, QButtonGroup, QStackedWidget, QMainWindow, QInputDialog,
                             QColorDialog, QSlider, QFrame, QSpacerItem, QSizePolicy, QProgressBar, QComboBox, QTextEdit)
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon
from PyQt5.QtCore import Qt, QSettings, QPropertyAnimation, QEasingCurve, QSize, QUrl, QEvent
from PyQt5.QtMultimedia import QSoundEffect
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import QDialog
import traceback

class DataManager:
    def __init__(self):
        if getattr(sys, 'frozen', False):
            # Eğer uygulama bir exe ise
            self.base_path = os.path.dirname(sys.executable)
            # Bir üst klasöre git
            self.base_path = os.path.dirname(self.base_path)
        else:
            # Uygulama normal bir Python betiği ise
            self.base_path = os.path.dirname(os.path.abspath(__file__))
        
        self.data_path = os.path.join(self.base_path, 'data')
        os.makedirs(self.data_path, exist_ok=True)
        
        print(f"Base path: {self.base_path}")
        print(f"Data path: {self.data_path}")

    def load_json(self, filename):
        file_path = os.path.join(self.data_path, filename)
        print(f"Attempting to load JSON from: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return {}

    def save_json(self, filename, data):
        file_path = os.path.join(self.data_path, filename)
        print(f"Saving JSON to: {file_path}")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

class CustomMessageBox(QDialog):
    def __init__(self, parent=None, title="", message=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(message))
        ok_button = QPushButton("Tamam")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)
        self.setLayout(layout)


class LearnWithQuiz(QMainWindow):
    def __init__(self):
        super().__init__()
        self.data_manager = DataManager()
        self.settings = QSettings('Learn With Quiz', 'AppSettings')
        self.load_words()
        self.load_mistake_words()
        self.load_theme()
        self.sound_volume = self.settings.value('sound_volume', 50, type=int)
        self.initUI()
        self.apply_theme()
        self.load_sounds()
        self.current_study_index = 0
        self.current_study_group = []
        self.load_extended_words()
        self.create_word_groups()
        self.quiz_groups = []
        self.study_page = None
        self.settings_page = None
        self.mistake_review_page = None
        self.review_word_label = None
        self.review_answer_input = None
        self.review_submit_button = None
        self.review_score_label = None
        self.review_progress_label = None
        self.create_study_page()
        self.create_settings_page()
        self.create_mistake_review_page()


    def get_base_path(self):
        if getattr(sys, 'frozen', False):
            # Eğer uygulama bir exe ise
            return sys._MEIPASS
        else:
            # Uygulama normal bir Python betiği ise
            return os.path.dirname(os.path.abspath(__file__))

    def get_data_path(self):
        if getattr(sys, 'frozen', False):
            # Eğer uygulama bir exe ise, kullanıcının belgeler klasörünü kullan
            return os.path.join(os.path.expanduser('~'), 'Documents', 'LearnWithQuiz')
        else:
            # Uygulama normal bir Python betiği ise, mevcut dizini kullan
            return os.path.join(self.base_path, 'data')

    def ensure_data_directory(self):
        os.makedirs(self.data_path, exist_ok=True)
    
    def load_extended_words(self):
        extended_words = self.data_manager.load_json('learnwithquiz_words_extended.json')
        self.extended_words = extended_words.get('words', [])
        if not self.extended_words:
            QMessageBox.warning(self, "Hata", "yokdil_fen_words_extended.json dosyası bulunamadı veya boş. Lütfen dosyayı kontrol edin.")

    def create_word_groups(self, group_size=50):
        self.word_groups = [self.extended_words[i:i+group_size] for i in range(0, len(self.extended_words), group_size)]

    def create_study_page(self):
        study_widget = QWidget()
        study_layout = QVBoxLayout(study_widget)

        # Grup seçici
        self.group_selector = QComboBox()
        self.group_selector.setFont(QFont('Arial', self.font_size))
        self.group_selector.currentIndexChanged.connect(self.load_study_group)
        study_layout.addWidget(self.group_selector)

        # Kelime gösterimi için frame
        word_frame = QFrame()
        word_frame.setObjectName("wordFrame")
        word_frame_layout = QVBoxLayout(word_frame)
        
        self.english_word_label = QLabel()
        self.english_word_label.setAlignment(Qt.AlignCenter)
        self.english_word_label.setFont(QFont('Arial', 24, QFont.Bold))
        word_frame_layout.addWidget(self.english_word_label)

        self.turkish_word_label = QLabel()
        self.turkish_word_label.setAlignment(Qt.AlignCenter)
        self.turkish_word_label.setFont(QFont('Arial', 18))
        word_frame_layout.addWidget(self.turkish_word_label)

        self.sentence_label = QLabel()
        self.sentence_label.setAlignment(Qt.AlignCenter)
        self.sentence_label.setFont(QFont('Arial', 14))
        self.sentence_label.setWordWrap(True)
        word_frame_layout.addWidget(self.sentence_label)

        study_layout.addWidget(word_frame)

        # İleri-geri ve ana menü butonları
        button_layout = QHBoxLayout()
        
        self.prev_button = QPushButton("Önceki")
        self.prev_button.clicked.connect(self.show_prev_study_word)
        button_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("Sonraki")
        self.next_button.clicked.connect(self.show_next_study_word)
        button_layout.addWidget(self.next_button)

        study_layout.addLayout(button_layout)

        main_menu_button = QPushButton("Ana Menüye Dön")
        main_menu_button.clicked.connect(self.return_to_main_menu)
        study_layout.addWidget(main_menu_button)

        return study_widget

    def load_study_group(self, index):
        if hasattr(self, 'current_study_group'):
            self.current_study_group = self.word_groups[index]
            random.shuffle(self.current_study_group)
            self.current_study_index = 0
            self.show_study_word()

    def update_group_selector(self):
        if hasattr(self, 'group_selector'):
            self.group_selector.clear()
            for i, group in enumerate(self.word_groups):
                self.group_selector.addItem(f"Grup {i+1} (Kelime {i*50+1}-{min((i+1)*50, len(self.extended_words))})")

    def show_study_word(self):
        if hasattr(self, 'current_study_group') and hasattr(self, 'current_study_index'):
            if self.current_study_index < len(self.current_study_group):
                word = self.current_study_group[self.current_study_index]
                self.english_word_label.setText(word['english'])
                self.turkish_word_label.setText(', '.join(word['turkish']))
                if word['sentences']:
                    sentence = random.choice(word['sentences'])
                    self.sentence_label.setText(f"EN: {sentence['english']}\nTR: {sentence['turkish']}")
                else:
                    self.sentence_label.setText("Bu kelime için örnek cümle bulunmamaktadır.")
            else:
                self.english_word_label.setText("Tamamlandı")
                self.turkish_word_label.setText("")
                self.sentence_label.setText("Bu gruptaki tüm kelimeler tamamlandı.")

    def show_prev_study_word(self):
        if self.current_study_index > 0:
            self.current_study_index -= 1
            self.show_study_word()

    def show_next_study_word(self):
        if self.current_study_index < len(self.current_study_group) - 1:
            self.current_study_index += 1
            self.show_study_word()
        else:
            QMessageBox.information(self, "Tamamlandı", "Bu gruptaki tüm kelimeler tamamlandı.")

    def show_word_study(self):
        study_page = self.create_study_page()
        if self.stack.indexOf(study_page) == -1:
            self.stack.addWidget(study_page)
        self.stack.setCurrentWidget(study_page)
        self.create_word_groups()
        self.update_group_selector()
        self.load_study_group(0)

    def start_word_study(self):
        if self.extended_words:
            self.create_study_page()  # Her seferinde yeni bir sayfa oluştur
            self.create_word_groups()
            self.update_group_selector()
            self.stack.setCurrentIndex(5)  # Kelime çalışması sayfasının indeksi
            self.load_study_group(0)  # İlk grubu yükle
        else:
            QMessageBox.warning(self, "Hata", "Kelime dosyası yüklenemedi. Lütfen yokdil_fen_words_extended.json dosyasını kontrol edin.")

    def initUI(self):
        self.setWindowTitle('Learn With Quiz: Dil Öğrenme Asistanı')
        self.setGeometry(100, 100, 1000, 800)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        self.create_main_menu()
        
    def return_to_main_menu(self):
        self.stack.setCurrentIndex(0)  # Ana menü her zaman ilk sayfadır
        
    def create_main_menu(self):
        menu_widget = QWidget()
        menu_layout = QVBoxLayout(menu_widget)

        title_label = QLabel('Learn With Quiz')
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont('Arial', 24, QFont.Bold))
        menu_layout.addWidget(title_label)

        buttons = [
            ('Kelime Çalışması', self.show_word_study),
            ('Yazılı Quiz', lambda: self.start_quiz(1)),
            ('Çoktan Seçmeli Quiz', lambda: self.start_quiz(2)),
            ('Hata Yapılan Kelimeleri Çalış', self.show_mistake_review),  # Bu satırı düzelttik
            ('Yeni Kelime Ekle', self.add_word),
            ('Ayarlar', self.show_settings)
        ]

        for text, func in buttons:
            button = QPushButton(text)
            button.clicked.connect(func)
            button.setMinimumHeight(50)
            button.setCursor(Qt.PointingHandCursor)
            menu_layout.addWidget(button)

        self.stack.addWidget(menu_widget)

    def open_settings(self):
        self.stack.setCurrentIndex(4)  # Ayarlar sayfasının indeksi

    def create_written_quiz(self):
        quiz_widget = QWidget()
        quiz_layout = QVBoxLayout(quiz_widget)

        word_frame = QFrame()
        word_frame.setObjectName("wordFrame")
        word_frame_layout = QVBoxLayout(word_frame)
        
        self.written_word_label = QLabel('')
        self.written_word_label.setAlignment(Qt.AlignCenter)
        self.written_word_label.setFont(QFont('Arial', 24, QFont.Bold))
        word_frame_layout.addWidget(self.written_word_label)

        quiz_layout.addWidget(word_frame)

        self.written_answer_input = QLineEdit()
        self.written_answer_input.setFont(QFont('Arial', 16))
        self.written_answer_input.returnPressed.connect(self.check_written_answer)
        quiz_layout.addWidget(self.written_answer_input)

        self.written_submit_button = QPushButton('Cevapla')
        self.written_submit_button.clicked.connect(self.check_written_answer)
        quiz_layout.addWidget(self.written_submit_button)

        score_progress_layout = QHBoxLayout()
        self.written_score_label = QLabel('Doğru: 0, Yanlış: 0')
        self.written_score_label.setFont(QFont('Arial', 16))
        self.written_progress_label = QLabel(f'İlerleme: 0/{self.total_words}')
        self.written_progress_label.setFont(QFont('Arial', 16))
        score_progress_layout.addWidget(self.written_score_label)
        score_progress_layout.addWidget(self.written_progress_label)
        quiz_layout.addLayout(score_progress_layout)

        self.written_progress_bar = QProgressBar()
        self.written_progress_bar.setRange(0, 100)
        self.written_progress_bar.setValue(0)
        quiz_layout.addWidget(self.written_progress_bar)

        back_button = QPushButton('Ana Menüye Dön')
        back_button.clicked.connect(self.return_to_main_menu)
        quiz_layout.addWidget(back_button)

        return quiz_widget

    def create_multiple_choice_quiz(self):
        quiz_widget = QWidget()
        quiz_layout = QVBoxLayout(quiz_widget)

        word_frame = QFrame()
        word_frame.setObjectName("wordFrame")
        word_frame_layout = QVBoxLayout(word_frame)
        
        self.mc_word_label = QLabel('')
        self.mc_word_label.setAlignment(Qt.AlignCenter)
        self.mc_word_label.setFont(QFont('Arial', 24, QFont.Bold))
        word_frame_layout.addWidget(self.mc_word_label)

        quiz_layout.addWidget(word_frame)

        self.radio_group = QButtonGroup()
        self.radio_buttons = []
        for i in range(4):
            radio = QRadioButton(f'Seçenek {i+1}')
            radio.setFont(QFont('Arial', 16))
            self.radio_group.addButton(radio, i)
            self.radio_buttons.append(radio)
            quiz_layout.addWidget(radio)

        self.mc_submit_button = QPushButton('Cevapla')
        self.mc_submit_button.clicked.connect(self.check_mc_answer)
        quiz_layout.addWidget(self.mc_submit_button)

        score_progress_layout = QHBoxLayout()
        self.mc_score_label = QLabel('Doğru: 0, Yanlış: 0')
        self.mc_score_label.setFont(QFont('Arial', 16))
        self.mc_progress_label = QLabel(f'İlerleme: 0/{self.total_words}')
        self.mc_progress_label.setFont(QFont('Arial', 16))
        score_progress_layout.addWidget(self.mc_score_label)
        score_progress_layout.addWidget(self.mc_progress_label)
        quiz_layout.addLayout(score_progress_layout)

        self.mc_progress_bar = QProgressBar()
        self.mc_progress_bar.setRange(0, 100)
        self.mc_progress_bar.setValue(0)
        quiz_layout.addWidget(self.mc_progress_bar)

        back_button = QPushButton('Ana Menüye Dön')
        back_button.clicked.connect(self.return_to_main_menu)
        quiz_layout.addWidget(back_button)

        return quiz_widget

    def eventFilter(self, source, event):
        if (event.type() == QEvent.KeyPress and
            event.key() == Qt.Key_Return and
            source in self.radio_buttons):
            self.check_mc_answer()
            return True
        return super().eventFilter(source, event)
    

    def create_settings_page(self):
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)

        # Koyu mod düğmesi
        self.dark_mode_toggle = QPushButton('Koyu Mod')
        self.dark_mode_toggle.setCheckable(True)
        self.dark_mode_toggle.setChecked(self.dark_mode)
        self.dark_mode_toggle.clicked.connect(self.toggle_dark_mode)
        settings_layout.addWidget(self.dark_mode_toggle)

        # Tema renk seçici
        color_button = QPushButton('Ana Tema Rengi Seç')
        color_button.clicked.connect(self.choose_theme_color)
        settings_layout.addWidget(color_button)

        # Yazı tipi boyutu ayarı
        font_size_slider = QSlider(Qt.Horizontal)
        font_size_slider.setMinimum(8)
        font_size_slider.setMaximum(24)
        font_size_slider.setValue(self.font_size)
        font_size_slider.valueChanged.connect(self.change_font_size)
        settings_layout.addWidget(QLabel('Yazı Tipi Boyutu:'))
        settings_layout.addWidget(font_size_slider)

        # Ses ayarı
        sound_slider = QSlider(Qt.Horizontal)
        sound_slider.setMinimum(0)
        sound_slider.setMaximum(100)
        sound_slider.setValue(self.sound_volume)
        sound_slider.valueChanged.connect(self.change_sound_volume)
        settings_layout.addWidget(QLabel('Ses Seviyesi:'))
        settings_layout.addWidget(sound_slider)

        # Ana menüye dönüş düğmesi
        back_button = QPushButton('Ana Menüye Dön')
        back_button.clicked.connect(self.return_to_main_menu)
        settings_layout.addWidget(back_button)

        return settings_widget

    def load_theme(self):
        self.dark_mode = self.settings.value('dark_mode', False, type=bool)
        self.theme_color = self.settings.value('theme_color', '#4CAF50')
        self.font_size = self.settings.value('font_size', 12, type=int)
    
    def load_sounds(self):
        sounds_path = os.path.join(os.path.dirname(self.data_manager.data_path), 'sounds')
        correct_sound_path = os.path.join(sounds_path, 'correct.wav')
        incorrect_sound_path = os.path.join(sounds_path, 'incorrect.wav')

        self.correct_sound = QSoundEffect(self)
        self.incorrect_sound = QSoundEffect(self)

        if os.path.exists(correct_sound_path):
            self.correct_sound.setSource(QUrl.fromLocalFile(correct_sound_path))
        else:
            print(f"Correct sound file does not exist: {correct_sound_path}")

        if os.path.exists(incorrect_sound_path):
            self.incorrect_sound.setSource(QUrl.fromLocalFile(incorrect_sound_path))
        else:
            print(f"Incorrect sound file does not exist: {incorrect_sound_path}")

        self.set_sound_volume(self.sound_volume)

    
    def set_sound_volume(self, volume):
        self.sound_volume = volume
        self.settings.setValue('sound_volume', volume)
        volume_float = volume / 100.0
        if self.correct_sound.isLoaded():
            self.correct_sound.setVolume(volume_float)
        if self.incorrect_sound.isLoaded():
            self.incorrect_sound.setVolume(volume_float)
        
    def play_sound(self, is_correct):
        sound = self.correct_sound if is_correct else self.incorrect_sound
        if sound.isLoaded():
            sound.play()
        else:
            print(f"{'Correct' if is_correct else 'Incorrect'} sound is not loaded")

    def change_sound_volume(self, volume):
        """self.sound_volume = volume
        self.settings.setValue('sound_volume', volume)
        # Ses seviyesini ayarla (QSound için doğrudan bir metod yok, bu yüzden sadece kaydediyoruz)"""
        self.set_sound_volume(volume)

    def apply_theme(self):
        if self.dark_mode:
            self.setStyleSheet(f"""
                QMainWindow, QWidget {{ background-color: #2c2c2c; color: white; }}
                QPushButton {{ 
                    background-color: {self.theme_color}; 
                    color: white; 
                    border: none; 
                    padding: 10px; 
                    border-radius: 5px; 
                    font-size: {self.font_size}px;
                }}
                QPushButton:hover {{ background-color: {self.lighten_color(self.theme_color, 1.1)}; }}
                QLabel {{ font-size: {self.font_size}px; color: white; }}
                QLineEdit {{ 
                    background-color: #3c3c3c; 
                    color: white; 
                    border: 1px solid #555; 
                    padding: 5px;
                    font-size: {self.font_size}px;
                }}
                #wordFrame {{
                    background-color: #3c3c3c;
                    border: 2px solid {self.theme_color};
                    border-radius: 10px;
                    padding: 20px;
                    margin: 20px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QMainWindow, QWidget {{ background-color: #f0f0f0; color: black; }}
                QPushButton {{ 
                    background-color: {self.theme_color}; 
                    color: white; 
                    border: none; 
                    padding: 10px; 
                    border-radius: 5px; 
                    font-size: {self.font_size}px;
                }}
                QPushButton:hover {{ background-color: {self.lighten_color(self.theme_color, 1.1)}; }}
                QLabel {{ font-size: {self.font_size}px; color: black; }}
                QLineEdit {{ 
                    background-color: white; 
                    color: black; 
                    border: 1px solid #ddd; 
                    padding: 5px;
                    font-size: {self.font_size}px;
                }}
                #wordFrame {{
                    background-color: white;
                    border: 2px solid {self.theme_color};
                    border-radius: 10px;
                    padding: 20px;
                    margin: 20px;
                }}
            """)

    def toggle_dark_mode(self):
        self.dark_mode = self.dark_mode_toggle.isChecked()
        self.settings.setValue('dark_mode', self.dark_mode)
        self.apply_theme()

    def choose_theme_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.theme_color = color.name()
            self.settings.setValue('theme_color', self.theme_color)
            self.apply_theme()

    def change_font_size(self, size):
        self.font_size = size
        self.settings.setValue('font_size', size)
        self.apply_theme()

    @staticmethod
    def lighten_color(color, factor=1.3):
        col = QColor(color)
        h, s, l, _ = col.getHsl()
        col.setHsl(h, s, min(int(l * factor), 255), col.alpha())
        return col.name()

    def load_words(self):
        self.words = self.data_manager.load_json('learnwithquiz_words.json')
        if not self.words:
            self.words = {
                "experiment": ["deney"],
                "hypothesis": ["hipotez"],
                "analysis": ["analiz"],
                "data": ["veri"],
                "research": ["araştırma"],
                "theory": ["teori"],
                "method": ["yöntem"],
                "result": ["sonuç"],
                "observation": ["gözlem"],
                "conclusion": ["sonuç", "çıkarım"]
            }
            self.data_manager.save_json('learnwithquiz_words.json', self.words)
        self.total_words = len(self.words)
        self.word_list = list(self.words.items())
        random.shuffle(self.word_list)
        self.current_index = 0
        self.correct_count = 0
        self.incorrect_count = 0

    def save_words(self):
        words_file = os.path.join(self.data_path, 'learnwithquiz_words.json')
        with open(words_file, 'w', encoding='utf-8') as f:
            json.dump({'words': list(self.words.values())}, f, ensure_ascii=False, indent=4)


    def create_quiz_groups(self, group_size=50):
        return [list(self.words.items())[i:i+group_size] for i in range(0, len(self.words), group_size)]

    def create_quiz_group_selector(self):
        group_selector = QComboBox()
        group_selector.setFont(QFont('Arial', self.font_size))
        for i, group in enumerate(self.quiz_groups):
            group_selector.addItem(f"Grup {i+1} (Kelime {i*50+1}-{min((i+1)*50, len(self.words))})")
        return group_selector
        
    def start_quiz(self, quiz_type):
        self.load_words()
        self.current_quiz_type = quiz_type
        
        self.quiz_groups = self.create_quiz_groups()
        
        if quiz_type == 1:
            quiz_widget = self.create_written_quiz()
        elif quiz_type == 2:
            quiz_widget = self.create_multiple_choice_quiz()
        
        group_selector = self.create_quiz_group_selector()
        group_selector.currentIndexChanged.connect(lambda index: self.load_quiz_group(index, quiz_type))
        quiz_widget.layout().insertWidget(0, group_selector)
        
        self.stack.addWidget(quiz_widget)
        self.stack.setCurrentWidget(quiz_widget)
        self.load_quiz_group(0, quiz_type)

    def load_quiz_group(self, index, quiz_type):
        self.current_group = self.quiz_groups[index]
        random.shuffle(self.current_group)
        self.current_index = 0
        self.correct_count = 0
        self.incorrect_count = 0
        self.next_word()

    def next_word(self):
        if self.current_index < len(self.current_group):
            self.current_word = self.current_group[self.current_index]
            if self.current_quiz_type == 1:  # Written quiz
                self.written_word_label.setText(f'Kelime: {self.current_word[0]}')
                self.written_answer_input.clear()
                self.written_answer_input.setFocus()
                self.written_progress_label.setText(f'İlerleme: {self.current_index + 1}/{len(self.current_group)}')
            elif self.current_quiz_type == 2:  # Multiple choice quiz
                self.mc_word_label.setText(f'Kelime: {self.current_word[0]}')
                self.mc_progress_label.setText(f'İlerleme: {self.current_index + 1}/{len(self.current_group)}')
                self.setup_mc_options()
            self.update_score()
        else:
            self.show_result()

    def setup_mc_options(self):
        correct_answer = random.choice(self.current_word[1])
        choices = [correct_answer]
        
        other_words = list(self.words.values())
        other_words.remove(self.current_word[1])
        wrong_answers = random.sample([item for sublist in other_words for item in sublist], 3)
        choices.extend(wrong_answers)
        random.shuffle(choices)

        for i, choice in enumerate(choices):
            self.radio_buttons[i].setText(choice)
            self.radio_buttons[i].setChecked(False)  # Şıkların işaretini kaldır
    
    def change_page(self, new_page):
        self.stack.setCurrentWidget(new_page)

    def check_answer(self):
        user_answer = self.answer_input.text().strip().lower()
        correct_answers = [ans.lower() for ans in self.current_word[1]]

        if user_answer in correct_answers:
            self.correct_count += 1
            QMessageBox.information(self, 'Doğru', 'Tebrikler, doğru cevap!')
        else:
            self.incorrect_count += 1
            QMessageBox.warning(self, 'Yanlış', f'Yanlış. Doğru cevap(lar): {", ".join(self.current_word[1])}')
            self.add_to_mistakes(self.current_word[0], self.current_word[1])

        self.update_score()
        self.current_index += 1
        self.next_word()

    def check_mc_answer(self):
        selected_answer = self.radio_group.checkedButton()
        if selected_answer:
            if selected_answer.text() in self.current_word[1]:
                self.correct_count += 1
                self.play_sound(True)
                CustomMessageBox(self, "Doğru", "Tebrikler, doğru cevap!").exec_()
                if self.current_word[0] in self.mistake_words:
                    self.mistake_words[self.current_word[0]]["correct_count"] += 1
                    if self.mistake_words[self.current_word[0]]["correct_count"] >= 2:
                        del self.mistake_words[self.current_word[0]]
                    self.save_mistake_words()
            else:
                self.incorrect_count += 1
                self.play_sound(False)
                CustomMessageBox(self, "Yanlış", f'Yanlış. Doğru cevap(lar): {", ".join(self.current_word[1])}').exec_()
                self.add_to_mistakes(self.current_word[0], self.current_word[1])
            
            self.update_score()
            self.current_index += 1
            
            # Radyo düğmelerinin işaretini kaldır
            for radio in self.radio_buttons:
                radio.setChecked(False)
            
            # QButtonGroup'un seçimini temizle
            self.radio_group.setExclusive(False)
            checked_button = self.radio_group.checkedButton()
            if checked_button:
                checked_button.setChecked(False)
            self.radio_group.setExclusive(True)
            
            self.next_word()
        else:
            CustomMessageBox(self, "Uyarı", "Lütfen bir cevap seçin.").exec_()
            
    def check_written_answer(self):
        user_answer = self.written_answer_input.text().strip().lower()
        correct_answers = [ans.lower() for ans in self.current_word[1]]

        if user_answer in correct_answers:
            self.correct_count += 1
            self.play_sound(True)
            CustomMessageBox(self, "Doğru", "Tebrikler, doğru cevap!").exec_()
            if self.current_word[0] in self.mistake_words:
                self.mistake_words[self.current_word[0]]["correct_count"] += 1
                if self.mistake_words[self.current_word[0]]["correct_count"] >= 2:
                    del self.mistake_words[self.current_word[0]]
                self.save_mistake_words()
        else:
            self.incorrect_count += 1
            self.play_sound(False)
            CustomMessageBox(self, "Yanlış", f'Yanlış. Doğru cevap(lar): {", ".join(self.current_word[1])}').exec_()
            self.add_to_mistakes(self.current_word[0], self.current_word[1])

        self.update_score()
        self.current_index += 1
        self.next_word()

    def update_score(self):
        total_answered = self.correct_count + self.incorrect_count
        score_text = f'Doğru: {self.correct_count}, Yanlış: {self.incorrect_count}'
        progress_text = f'İlerleme: {self.current_index + 1}/{self.total_words}'
        progress_percentage = (self.correct_count / total_answered * 100) if total_answered > 0 else 0

        if self.current_quiz_type == 1:
            self.written_score_label.setText(score_text)
            self.written_progress_label.setText(progress_text)
            self.written_progress_bar.setValue(int(progress_percentage))
        elif self.current_quiz_type == 2:
            self.mc_score_label.setText(score_text)
            self.mc_progress_label.setText(progress_text)
            self.mc_progress_bar.setValue(int(progress_percentage))

    def show_settings(self):
        settings_page = self.create_settings_page()
        if self.stack.indexOf(settings_page) == -1:
            self.stack.addWidget(settings_page)
        self.stack.setCurrentWidget(settings_page)

    def show_result(self):
        QMessageBox.information(self, 'Quiz Bitti', 
                                f'Quiz bitti. Toplam {self.total_words} kelimeden '
                                f'{self.correct_count} doğru, {self.incorrect_count} yanlış yaptınız.')
        self.stack.setCurrentIndex(0)  # Ana menüye dön

    def add_word(self):
        english, ok = QInputDialog.getText(self, 'Yeni Kelime', 'İngilizce kelimeyi girin:')
        if ok and english:
            if english in self.words:
                reply = QMessageBox.question(self, 'Kelime Zaten Var', 
                                            f'"{english}" kelimesi zaten mevcut.\nMevcut anlamı: {", ".join(self.words[english])}\n\nYeni bir anlam eklemek ister misiniz?',
                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    new_meaning, ok = QInputDialog.getText(self, 'Yeni Anlam', 'Yeni Türkçe anlamı girin:')
                    if ok and new_meaning:
                        self.words[english].append(new_meaning)
                else:
                    return
            else:
                turkish, ok = QInputDialog.getText(self, 'Yeni Kelime', 'Türkçe anlamını girin (birden fazla anlam için virgülle ayırın):')
                if ok and turkish:
                    self.words[english] = turkish.split(',')

            # Cümle ekleme
            add_sentence = QMessageBox.question(self, 'Cümle Ekle', 'Bu kelime için örnek cümle eklemek ister misiniz?',
                                                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if add_sentence == QMessageBox.Yes:
                english_sentence, ok = QInputDialog.getText(self, 'İngilizce Cümle', 'İngilizce örnek cümleyi girin:')
                if ok and english_sentence:
                    turkish_sentence, ok = QInputDialog.getText(self, 'Türkçe Çeviri', 'Cümlenin Türkçe çevirisini girin:')
                    if ok and turkish_sentence:
                        if not isinstance(self.words[english], dict):
                            self.words[english] = {"turkish": self.words[english], "sentences": []}
                        if "sentences" not in self.words[english]:
                            self.words[english]["sentences"] = []
                        self.words[english]["sentences"].append({
                            'english': english_sentence,
                            'turkish': turkish_sentence
                        })

            self.data_manager.save_json('learnwithquiz_words.json', self.words)
            self.total_words = len(self.words)
            QMessageBox.information(self, 'Kelime Eklendi', 'Yeni kelime başarıyla eklendi.')
            self.load_words()  # Kelime listesini güncelle
    
    def create_mistake_review_page(self):
        if self.mistake_review_page is None:
            self.mistake_review_page = QWidget()
            review_layout = QVBoxLayout(self.mistake_review_page)

            self.review_word_label = QLabel('Kelime:')
            self.review_word_label.setFont(QFont('Arial', 18))
            review_layout.addWidget(self.review_word_label)

            self.review_answer_input = QLineEdit()
            self.review_answer_input.setFont(QFont('Arial', 16))
            self.review_answer_input.returnPressed.connect(self.check_review_answer)
            review_layout.addWidget(self.review_answer_input)

            self.review_submit_button = QPushButton('Cevapla')
            self.review_submit_button.clicked.connect(self.check_review_answer)
            review_layout.addWidget(self.review_submit_button)

            self.review_score_label = QLabel('Doğru: 0, Yanlış: 0')
            self.review_score_label.setFont(QFont('Arial', 16))
            review_layout.addWidget(self.review_score_label)

            self.review_progress_label = QLabel('İlerleme: 0/0')
            self.review_progress_label.setFont(QFont('Arial', 16))
            review_layout.addWidget(self.review_progress_label)

            back_button = QPushButton('Ana Menüye Dön')
            back_button.clicked.connect(self.return_to_main_menu)
            review_layout.addWidget(back_button)

        return self.mistake_review_page
    
    def load_mistake_words(self):
        self.mistake_words = self.data_manager.load_json('learnwithquiz_mistake_words.json')
        
        # Mevcut verileri yeni formata dönüştür
        for word, data in self.mistake_words.items():
            if isinstance(data, list):
                self.mistake_words[word] = {
                    "correct_answers": data,
                    "correct_count": 0
                }

    def save_mistake_words(self):
        self.data_manager.save_json('learnwithquiz_mistake_words.json', self.mistake_words)


    def show_mistake_review(self):
        try:
            
            if not self.mistake_words:
                QMessageBox.information(self, 'Bilgi', 'Hata yapılan kelime bulunmamaktadır.')
                return
            
            if self.mistake_review_page is None:
                self.create_mistake_review_page()
            
            if self.stack.indexOf(self.mistake_review_page) == -1:
                self.stack.addWidget(self.mistake_review_page)
            
            self.stack.setCurrentWidget(self.mistake_review_page)
            self.start_mistake_review()
        except Exception as e:
            print(f"show_mistake_review'da hata oluştu: {str(e)}")
            print(traceback.format_exc())
            QMessageBox.critical(self, 'Hata', f'Bir hata oluştu: {str(e)}')

    def add_to_mistakes(self, word, correct_answers):
        if word not in self.mistake_words:
            self.mistake_words[word] = {"correct_answers": correct_answers, "correct_count": 0}
        else:
            self.mistake_words[word]["correct_count"] = 0  # Yanlış yapıldıysa sayacı sıfırla
        self.save_mistake_words()

    def start_mistake_review(self):
        if not self.mistake_words:
            QMessageBox.information(self, 'Bilgi', 'Hata yapılan kelime bulunmamaktadır.')
            return
        self.review_word_list = list(self.mistake_words.items())
        random.shuffle(self.review_word_list)
        self.review_index = 0
        self.review_correct_count = 0
        self.review_incorrect_count = 0
        self.next_review_word()

    def next_review_word(self):
        if self.review_index < len(self.review_word_list):
            self.current_review_word = self.review_word_list[self.review_index]
            self.review_word_label.setText(f'Kelime: {self.current_review_word[0]}')
            self.review_answer_input.clear()
            self.review_answer_input.setFocus()
            self.review_progress_label.setText(f'İlerleme: {self.review_index + 1}/{len(self.review_word_list)}')
        else:
            self.show_review_result()

    def check_review_answer(self):
        user_answer = self.review_answer_input.text().strip().lower()
        correct_answers = [ans.lower() for ans in self.mistake_words[self.current_review_word[0]]["correct_answers"]]

        if user_answer in correct_answers:
            self.review_correct_count += 1
            QMessageBox.information(self, 'Doğru', 'Tebrikler, doğru cevap!')
            self.mistake_words[self.current_review_word[0]]["correct_count"] += 1
            if self.mistake_words[self.current_review_word[0]]["correct_count"] >= 2:
                del self.mistake_words[self.current_review_word[0]]
        else:
            self.review_incorrect_count += 1
            QMessageBox.warning(self, 'Yanlış', f'Yanlış. Doğru cevap(lar): {", ".join(correct_answers)}')
            self.mistake_words[self.current_review_word[0]]["correct_count"] = 0  # Yanlış yapıldıysa sayacı sıfırla

        self.save_mistake_words()
        self.update_review_score()
        self.review_index += 1
        self.next_review_word()

    def update_review_score(self):
        score_text = f'Doğru: {self.review_correct_count}, Yanlış: {self.review_incorrect_count}'
        self.review_score_label.setText(score_text)

    def show_review_result(self):
        QMessageBox.information(self, 'İnceleme Bitti', 
                                f'İnceleme bitti. Toplam {len(self.review_word_list)} kelimeden '
                                f'{self.review_correct_count} doğru, {self.review_incorrect_count} yanlış yaptınız.')
        self.stack.setCurrentIndex(0)  # Ana menüye dön

if __name__ == '__main__':
    # Set the attribute before creating QApplication
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    ex = LearnWithQuiz()
    ex.show()
    sys.exit(app.exec_())