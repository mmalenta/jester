from csv import reader, writer
from glob import glob
from os import path
from os.path import basename
from shutil import move

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap
from numpy import array, histogram

from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QLabel, QPushButton
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import Qt

from pyqtgraph import mkPen, PlotWidget

class CandClassifier(QWidget):

    def __init__(self, directory, extension):

        super().__init__()

        self._directory = directory
        self._cand_plots = sorted(glob(path.join(directory, "*" + extension)))
        self._total_cands = len(self._cand_plots)
        self._current_cand = 0

        self._rfi_data = []
        self._cand_data = []
        #self._class_writer = writer(open(path.join(directory, "results.csv"),
        #                            "w", buffering=1), delimiter=",")

        self._stats_window = StatsWindow()

        main_box = QVBoxLayout()
        main_box.setContentsMargins(10, 0, 10, 0)
        main_box.setSpacing(0)

        # Because adding QPixmap to layout directly is not a thing
        self._plot_label = QLabel()
        main_box.addWidget(self._plot_label)

        stats_box = QHBoxLayout()
        stats_box.setContentsMargins(0, 0, 0, 0)

        self._rfi_count_label = QLabel("RFI: 0")
        self._rfi_count_label.setStyleSheet("font-weight: bold;\
                                        font-size: 20px")
        self._cand_count_label = QLabel("Candidates: 0")
        self._cand_count_label.setStyleSheet("font-weight: bold;\
                                            font-size: 20px")
        
        stats_box.addWidget(self._rfi_count_label)
        stats_box.addWidget(self._cand_count_label)
        main_box.addLayout(stats_box)

        self._cand_label = QLabel()
        self._cand_label.setStyleSheet("font-weight: bold;\
                                        font-size: 20px")
        main_box.addWidget(self._cand_label)

        buttons_box = QHBoxLayout()
        cand_box = QHBoxLayout()
        self._rfi_button = QPushButton()
        self._rfi_button.setText("RFI")
        self._rfi_button.clicked.connect(self._rfi_press)
        self._rfi_button.setFixedSize(250, 50)
        self._rfi_button.setStyleSheet("background-color: red;\
                                        font-weight: bold;\
                                        font-variant: small-caps;\
                                        font-size: 25px")
        cand_box.addWidget(self._rfi_button)
        self._cand_button = QPushButton()
        self._cand_button.setText("Candidate")
        self._cand_button.clicked.connect(self._cand_press)
        self._cand_button.setFixedSize(250, 50)
        self._cand_button.setStyleSheet("background-color: green;\
                                        font-weight: bold;\
                                        font-variant: small-caps;\
                                        font-size: 25px")
        cand_box.addWidget(self._cand_button)
        cand_box.setContentsMargins(0, 0, 30, 0)

        nav_box = QHBoxLayout()
        self._skip_start_button = QPushButton()
        self._skip_start_button.setText("|<")
        self._skip_start_button.setFixedWidth(25)
        self._skip_start_button.clicked.connect(self._skip_start_press)
        nav_box.addWidget(self._skip_start_button)
        self._prev_skip_button = QPushButton()
        self._prev_skip_button.setText("<<")
        self._prev_skip_button.setFixedWidth(40)
        self._prev_skip_button.clicked.connect(self._previous_skip_press)
        nav_box.addWidget(self._prev_skip_button)
        self._prev_button = QPushButton()
        self._prev_button.setText("<")
        self._prev_button.clicked.connect(self._previous_press)
        nav_box.addWidget(self._prev_button)
        self._next_button = QPushButton()
        self._next_button.setText(">")
        self._next_button.clicked.connect(self._next_press)
        nav_box.addWidget(self._next_button)
        self._next_skip_button = QPushButton()
        self._next_skip_button.setText(">>")
        self._next_skip_button.setFixedWidth(40)
        self._next_skip_button.clicked.connect(self._next_skip_press)
        nav_box.addWidget(self._next_skip_button)
        self._skip_end_button = QPushButton()
        self._skip_end_button.setText(">|")
        self._skip_end_button.setFixedWidth(25)
        self._skip_end_button.clicked.connect(self._skip_end_press)
        nav_box.addWidget(self._skip_end_button)
        nav_box.setContentsMargins(0, 0, 30, 0)

        buttons_box.addLayout(cand_box)
        buttons_box.addLayout(nav_box)

        extra_buttons = QVBoxLayout()
        self._stats_button = QPushButton()
        self._stats_button.clicked.connect(self._open_stats)
        self._stats_button.setText("Open Statistics")
        extra_buttons.addWidget(self._stats_button)
        buttons_box.addLayout(extra_buttons)
        main_box.addLayout(buttons_box)

        self.setLayout(main_box)
        self.setGeometry(150, 150, 1024, 768)
        # In reality we should set it properly with
        # setMinimum/MaximumSize() functions, based on the plot size
        self.setFixedSize(QSize(1024, 620))
        self.setWindowTitle("MeerTRAP candidate classifier")
        self.show()

        if len(self._cand_plots) > 0:
            self._show_cand()
        else:
            self._cand_label.setText("No candidates to view")

    def _save_data(self):

        foo = 1

    def _show_cand(self, idx = 0):

        if (idx < self._total_cands) and (idx >= 0):
            cand_map = QPixmap(self._cand_plots[idx])
            self._plot_label.setPixmap(cand_map)
            self._current_cand = idx
            self._cand_label.setText(f"{self._current_cand + 1}"
                                    + f" out of {self._total_cands}:"
                                    + f" {basename(self._cand_plots[idx])}")

    def _open_stats(self):

        if not self._stats_window.isVisible():
            self._stats_window.show()
            self._stats_button.setText("Close Statistics")
        else:
            self._stats_window.hide()
            self._stats_button.setText("Open Statistics")

    def keyPressEvent(self, event):

        route = {
            Qt.Key_A: self._rfi_press,
            Qt.Key_D: self._cand_press,
            Qt.Key_Z: self._previous_press,
            Qt.Key_X: self._next_press,
            Qt.Key_PageDown: self._previous_skip_press,
            Qt.Key_PageUp: self._next_skip_press,
            Qt.Key_Home: self._skip_start_press,
            Qt.Key_End: self._skip_end_press
        }

        pressed = event.key()
        function = route.get(pressed)
        if function:
            return function(event)

    def _update_list(self, idx, class_type):

        cand_name = basename(self._cand_plots[idx])
        split_cand = cand_name.split("_")
        cand_dm = float(split_cand[2])
        
        cand = (idx, cand_dm)

        if class_type == "rfi":
            if cand in self._cand_data:
                self._cand_data.remove(cand)
                self._rfi_data.append(cand)
                self._replace_csv(cand_name, 0)

            if cand not in self._rfi_data:
                self._rfi_data.append(cand)
                self._add_csv(cand_name, 0)
        else:
            if cand in self._rfi_data:
                self._rfi_data.remove(cand)
                self._cand_data.append(cand)
                self._replace_csv(cand_name, 1)

            if cand not in self._cand_data:
                self._cand_data.append(cand)
                self._add_csv(cand_name, 1)

        self._rfi_count_label.setText(f"RFI: {len(self._rfi_data)}")
        self._cand_count_label.setText(f"Candidates: {len(self._cand_data)}")

        self._stats_window._update(self._rfi_data, self._cand_data)

    def _replace_csv(self, cand_name, new_label):

        with open(path.join(self._directory, "results.csv"),
                            "r", buffering=1) as of,\
             open(path.join(self._directory, "results.csv.tmp"),
                            "a", buffering=1) as nf:
            
            old_csv = reader(of, delimiter=",")
            new_csv = writer(nf, delimiter=",")

            for cand in old_csv:
                if cand[0] != cand_name:
                    new_csv.writerow([cand[0], cand[1]])
                else:
                    new_csv.writerow([cand[0], new_label])

        move(path.join(self._directory, "results.csv.tmp"),
             path.join(self._directory, "results.csv"))

    def _add_csv(self, cand_name, label):

        with open(path.join(self._directory, "results.csv"),
                            "a", buffering=1) as cf:
            cand_csv = writer(cf, delimiter=",")
            cand_csv.writerow([cand_name, label])

    def _rfi_press(self, event):
        self._update_list(self._current_cand, "rfi")
        self._show_cand(self._current_cand + 1)

    def _cand_press(self, event):
        self._update_list(self._current_cand, "camd")
        self._show_cand(self._current_cand + 1)

    def _next_press(self, event):
        self._show_cand(self._current_cand + 1)

    def _previous_press(self, event):
        self._show_cand(self._current_cand - 1)

    def _previous_skip_press(self, event):
         idx = max(self._current_cand - 5, 0)
         self._show_cand(idx)

    def _next_skip_press(self, event):
        idx = min(self._current_cand + 5, self._total_cands - 1)
        self._show_cand(idx)

    def _skip_start_press(self, event):
        self._show_cand(0)

    def _skip_end_press(self, event):
        self._show_cand(self._total_cands - 1)

class StatsWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.setGeometry(150 + 1024, 150, 800, 400)


        self.graph_rfi = PlotWidget()
        self.graph_rfi.setBackground("w")
        self.graph_rfi.setTitle("RFI", color="k")
        self.graph_rfi.plot = self.graph_rfi.plot([0,0], [0],
                                                  pen=mkPen('k', width=1),
                                                  stepMode=True)

        self.graph_cand = PlotWidget()
        self.graph_cand.setBackground("w")
        self.graph_cand.setTitle("Candidates", color="k")
        self.graph_cand.plot = self.graph_cand.plot([0,0], [0],
                                                  pen=mkPen('k', width=1),
                                                  stepMode=True)

        hbox = QHBoxLayout()
        hbox.addWidget(self.graph_rfi)
        hbox.addWidget(self.graph_cand)

        self.setLayout(hbox)

    def _update(self, rfi_data, cand_data):


        y_rfi, x_rfi = histogram([cand[1] for cand in rfi_data],
                                 bins=min(len(rfi_data) + 1, 100))
        self.graph_rfi.plot.setData(x_rfi, y_rfi)

        y_cand, x_cand = histogram([cand[1] for cand in cand_data],
                                   bins=min(len(cand_data) + 1, 100))
        self.graph_cand.plot.setData(x_cand, y_cand)