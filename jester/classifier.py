from csv import reader, writer
from glob import glob
from numpy import array, histogram, linspace
from os import path
from os.path import basename, isfile
from shutil import move

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap

from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QComboBox, QLabel, QLineEdit, QMessageBox
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import Qt

from pyqtgraph import mkPen, PlotWidget

class CandClassifier(QWidget):

    def __init__(self, directory, output, extension):

        super().__init__()

        print()

        self._directory = directory
        self._output_file_name = output
        self._cand_plots = sorted(glob(path.join(directory, "*" + extension)))
        self._total_cands = len(self._cand_plots)

        self._cands_params = [{"mjd": float(basename(cand).split("_")[0]), "dm": float(basename(cand).split("_")[2])} for cand in self._cand_plots]
        self._current_cand = 0
        self._rfi_data = []
        self._cand_data = []

        self._stats_window = StatsWindow()
        self._stats_window.update_dist_plot([cand["dm"] for cand in self._cands_params])
        self._stats_window.apply_limits_button.clicked.connect(self._get_limits)
        self._stats_window.limits_choice.currentTextChanged.connect(self._change_source)

        self._help_window = HelpWindow()
        self._examples_window = ExamplesWindow()

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
        self._cand_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
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
        self._examples_button = QPushButton()
        self._examples_button.clicked.connect(self._open_examples)
        self._examples_button.setText("Examples")
        extra_buttons.addWidget(self._examples_button)
        self._help_button = QPushButton()
        self._help_button.clicked.connect(self._open_help)
        self._help_button.setText("Help")
        extra_buttons.addWidget(self._help_button)
        buttons_box.addLayout(extra_buttons)
        main_box.addLayout(buttons_box)

        self.setLayout(main_box)
        self.setGeometry(150, 150, 1024, 768)
        self.setWindowTitle("MeerTRAP candidate classifier")
        self.show()

        if len(self._cand_plots) > 0:
            self._show_cand()
        else:
            self._cand_label.setText("No candidates to view")
    
    """
        if isfile(path.join(self._directory, self._output_file_name)):
            done = 0
            with open(path.join(self._directory, self._output_file_name)) as df:
                done = sum(1 for line in df)

            if done > 0:
                self._resume_dialog(done, self._output_file_name)

    def _resume_dialog(self, done, file_name):

        done_box = QMessageBox()
        done_box.setIcon(QMessageBox.Information)
        done_box.setText(f"File {file_name} already exists with"
                         + f"{done} candidates.\n"
                         + "Would you like to load it?")
        done_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

        done_value = done_box.exec()
        
        if done_value == QMessageBox.Yes:
            self._reload_csv()
            self._show_cand(min(done, self._total_cands - 1))

    def _reload_csv():

        with open(path.join(self._directory, self._output_file_name)) as df:
            done_reader = reader(df, delimiter=",")

            for done in done_reader:
                filename = [0]
                done = [1]
    
    """

    def _change_source(self, source):

        self._stats_window.update_dist_plot([cand[source.lower()] for cand in self._cands_params], source == "MJD")

    def _get_limits(self):

        limit_type = self._stats_window.limits_choice.currentText()
        lower_limit = float(self._stats_window.start_limit.text())
        upper_limit = float(self._stats_window.end_limit.text())

        idx = 0
        if limit_type == "DM":
            idx = 2

        remaining_plots = self._cand_plots[self._current_cand:]
        passed_remaining_plots = [cand for cand in remaining_plots if not ((float(basename(cand).split("_")[idx]) >= lower_limit) and (float(basename(cand).split("_")[idx]) < upper_limit))]

        removed = len(remaining_plots) - len(passed_remaining_plots)
        self._stats_window.remove_label.setText(f"Removed {removed} candidates")

        del self._cand_plots[self._current_cand:]

        self._cand_plots.extend(passed_remaining_plots)
        self._total_cands = len(self._cand_plots)
        self._cands_params = [{"mjd": float(basename(cand).split("_")[0]), "dm": float(basename(cand).split("_")[2])} for cand in self._cand_plots]

        self._stats_window.update_dist_plot([cand[limit_type.lower()] for cand in self._cands_params], limit_type == "MJD")
        self._show_cand(self._current_cand)

    def _show_cand(self, idx = 0):

        if (idx == 0):

            cand_map = QPixmap(self._cand_plots[idx])
            img_width = cand_map.width()
            img_height = cand_map.height()

            window_width = max(img_width, 1024)
            window_height = max(img_height + 150, 620)
            self.setFixedSize(QSize(window_width, window_height))

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

    def _open_help(self):

        if not self._help_window.isVisible():
            self._help_window.show()
        else:
            self._help_window.hide()

    def _open_examples(self):

        if not self._examples_window.isVisible():
            self._examples_window.show()
        else:
            self._examples_window.hide()

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

        with open(path.join(self._directory, self._output_file_name),
                            "r", buffering=1) as of,\
             open(path.join(self._directory, self._output_file_name + ".tmp"),
                            "a", buffering=1) as nf:
            
            old_csv = reader(of, delimiter=",")
            new_csv = writer(nf, delimiter=",")

            for cand in old_csv:
                if cand[0] != cand_name:
                    new_csv.writerow([cand[0], cand[1]])
                else:
                    new_csv.writerow([cand[0], new_label])

        move(path.join(self._directory, self._output_file_name + ".tmp"),
             path.join(self._directory, self._output_file_name))

    def _add_csv(self, cand_name, label):

        with open(path.join(self._directory, self._output_file_name),
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
        self.setGeometry(150 + 1024, 150, 800, 600)

        main_box = QVBoxLayout()

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

        self.dist_plot = PlotWidget()
        self.dist_plot.setMouseEnabled(y=False)
        self.dist_plot.setBackground("w")
        self.dist_plot.setTitle("Full distribution", color="k")
        self.dist_plot.plot = self.dist_plot.plot([0,0], [0],
                                                  pen=mkPen('k', width=1),
                                                  stepMode=True)


        plots_box = QHBoxLayout()
        plots_box.addWidget(self.graph_rfi)
        plots_box.addWidget(self.graph_cand)
        main_box.addLayout(plots_box)
        main_box.addWidget(self.dist_plot)

        limits_box = QHBoxLayout()
        limits_box.setAlignment(Qt.AlignLeft)
        
        self.limits_choice = QComboBox()
        self.limits_choice.addItems(["DM", "MJD"])
        self.limits_choice.setFixedWidth(100)
        limits_box.addWidget(self.limits_choice)
        self.start_limit = QLineEdit()
        self.start_limit.setPlaceholderText("from")
        self.start_limit.setFixedWidth(150)
        limits_box.addWidget(self.start_limit)
        self.end_limit = QLineEdit()
        self.end_limit.setPlaceholderText("to")
        self.end_limit.setFixedWidth(150)
        limits_box.addWidget(self.end_limit)
        self.apply_limits_button = QPushButton()
        self.apply_limits_button.setFixedWidth(150)
        self.apply_limits_button.setText("Remove limits")
        limits_box.addWidget(self.apply_limits_button)
        self.remove_label = QLabel()
        limits_box.addWidget(self.remove_label)
        main_box.addLayout(limits_box)
        

        self.setLayout(main_box)

    def _update(self, rfi_data, cand_data):

        y_rfi, x_rfi = histogram([cand[1] for cand in rfi_data],
                                 bins=min(len(rfi_data) + 1, 100))
        self.graph_rfi.plot.setData(x_rfi, y_rfi)

        y_cand, x_cand = histogram([cand[1] for cand in cand_data],
                                   bins=min(len(cand_data) + 1, 100))
        self.graph_cand.plot.setData(x_cand, y_cand)

    def update_dist_plot(self, data, extra_dec=False):

        y_dist, x_dist = histogram(data, bins=100)
        ax = self.dist_plot.getAxis("bottom")

        min_val = min(data)
        max_val = max(data)
        tick_vals = linspace(min_val, max_val, num=6)
        decimals = 2 + extra_dec * 4
        ticks = [(val, "{:.{dec}f}".format(val, dec=decimals)) for val in tick_vals]
        ax.setTicks( [ticks, []])
        ax.setStyle(tickLength=-5)
        self.dist_plot.plot.setData(x_dist, y_dist)
        self.dist_plot.autoRange()

class HelpWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setGeometry(130, 130, 300, 300)

        help_contents = QVBoxLayout()
        help_label = QLabel()
        help_label.setText("RFI: A\nCandidate: D\nPrevious: Z\nNext: X\nBack 5: PgDown\nForward 5: PgUp\nBack to start: Home\nSkip to end: End")
        help_contents.addWidget(help_label)
        self.setLayout(help_contents)

class ExamplesWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.setGeometry(100, 200, 1024, 600)
        # In reality we should set it properly with
        # setMinimum/MaximumSize() functions, based on the plot size
        self.setFixedSize(QSize(1024, 600))

        self._example_descriptions = []

        with open(path.join(path.dirname(path.realpath(__file__)), "..", "./examples", "notes")) as nf:
            notes_reader = reader(nf, delimiter=",")

            for note in notes_reader:
                self._example_descriptions.append({"file": note[0], "label": note[1], "description": note[2]})
        
        self._total_examples = len(self._example_descriptions)
        self._current_example = 0

        example_layout = QVBoxLayout()
        self._plot_label = QLabel()
        example_layout.addWidget(self._plot_label)
        nav_box = QHBoxLayout()
        nav_box.setAlignment(Qt.AlignRight)
        self._description_label = QLabel()
        nav_box.addWidget(self._description_label)
        self._prev_button = QPushButton()
        self._prev_button.setText("<")
        self._prev_button.clicked.connect(self._previous_press)
        self._prev_button.setFixedWidth(100)
        nav_box.addWidget(self._prev_button)
        self._next_button = QPushButton()
        self._next_button.setText(">")
        self._next_button.clicked.connect(self._next_press)
        self._next_button.setFixedWidth(100)
        nav_box.addWidget(self._next_button)
        example_layout.addLayout(nav_box)
        self.setLayout(example_layout)

        self._show_example()

    def _show_example(self, idx = 0):

        if (idx < self._total_examples) and (idx >= 0):
            cand = self._example_descriptions[idx]
            cand_map = QPixmap(path.join(path.dirname(path.realpath(__file__)), "..", "examples", cand["file"]))
            self._plot_label.setPixmap(cand_map)
            self._description_label.setText(f"{idx + 1}/{self._total_examples} Label {cand['label']}: {cand['description']}")
            self._current_example = idx

    def _next_press(self, event):
        self._show_example(self._current_example + 1)

    def _previous_press(self, event):
        self._show_example(self._current_example - 1)