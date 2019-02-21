from FlatCAMTool import FlatCAMTool
from copy import copy,deepcopy
from ObjectCollection import *
from FlatCAMApp import *
from PyQt5 import QtGui, QtCore, QtWidgets
from GUIElements import IntEntry, RadioSet, LengthEntry

from FlatCAMObj import FlatCAMGeometry, FlatCAMExcellon, FlatCAMGerber


class ToolSolderPaste(FlatCAMTool):

    toolName = "Solder Paste Tool"

    def __init__(self, app):
        FlatCAMTool.__init__(self, app)

        ## Title
        title_label = QtWidgets.QLabel("%s" % self.toolName)
        title_label.setStyleSheet("""
                        QLabel
                        {
                            font-size: 16px;
                            font-weight: bold;
                        }
                        """)
        self.layout.addWidget(title_label)

        ## Form Layout
        obj_form_layout = QtWidgets.QFormLayout()
        self.layout.addLayout(obj_form_layout)

        ## Gerber Object to be used for solderpaste dispensing
        self.obj_combo = QtWidgets.QComboBox()
        self.obj_combo.setModel(self.app.collection)
        self.obj_combo.setRootModelIndex(self.app.collection.index(0, 0, QtCore.QModelIndex()))
        self.obj_combo.setCurrentIndex(1)

        self.object_label = QtWidgets.QLabel("Gerber:   ")
        self.object_label.setToolTip(
            "Gerber Solder paste object.                        "
        )
        obj_form_layout.addRow(self.object_label, self.obj_combo)

        #### Tools ####
        self.tools_table_label = QtWidgets.QLabel('<b>Tools Table</b>')
        self.tools_table_label.setToolTip(
            "Tools pool from which the algorithm\n"
            "will pick the ones used for dispensing solder paste."
        )
        self.layout.addWidget(self.tools_table_label)

        self.tools_table = FCTable()
        self.layout.addWidget(self.tools_table)

        self.tools_table.setColumnCount(3)
        self.tools_table.setHorizontalHeaderLabels(['#', 'Diameter', ''])
        self.tools_table.setColumnHidden(2, True)
        self.tools_table.setSortingEnabled(False)
        # self.tools_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

        self.tools_table.horizontalHeaderItem(0).setToolTip(
            "This is the Tool Number.\n"
            "The solder dispensing will start with the tool with the biggest \n"
            "diameter, continuing until there are no more Nozzle tools.\n"
            "If there are no longer tools but there are still pads not covered\n "
            "with solder paste, the app will issue a warning message box."
            )
        self.tools_table.horizontalHeaderItem(1).setToolTip(
            "Nozzle tool Diameter. It's value (in current FlatCAM units)\n"
            "is the width of the solder paste dispensed.")

        self.empty_label = QtWidgets.QLabel('')
        self.layout.addWidget(self.empty_label)

        #### Add a new Tool ####
        hlay_tools = QtWidgets.QHBoxLayout()
        self.layout.addLayout(hlay_tools)

        self.addtool_entry_lbl = QtWidgets.QLabel('<b>New Nozzle Tool:</b>')
        self.addtool_entry_lbl.setToolTip(
            "Diameter for the new Nozzle tool to add in the Tool Table"
        )
        self.addtool_entry = FCEntry()

        # hlay.addWidget(self.addtool_label)
        # hlay.addStretch()
        hlay_tools.addWidget(self.addtool_entry_lbl)
        hlay_tools.addWidget(self.addtool_entry)

        grid0 = QtWidgets.QGridLayout()
        self.layout.addLayout(grid0)

        self.addtool_btn = QtWidgets.QPushButton('Add')
        self.addtool_btn.setToolTip(
            "Add a new nozzle tool to the Tool Table\n"
            "with the diameter specified above."
        )

        self.deltool_btn = QtWidgets.QPushButton('Delete')
        self.deltool_btn.setToolTip(
            "Delete a selection of tools in the Tool Table\n"
            "by first selecting a row(s) in the Tool Table."
        )

        self.soldergeo_btn = QtWidgets.QPushButton("Generate Geo")
        self.soldergeo_btn.setToolTip(
            "Generate solder paste dispensing geometry."
        )

        step1_lbl = QtWidgets.QLabel("<b>STEP 1:</b>")
        step1_lbl.setToolTip(
            "First step is to select a number of nozzle tools for usage\n"
            "and then create a solder paste dispensing geometry out of an\n"
            "Solder Paste Mask Gerber file."
        )

        grid0.addWidget(self.addtool_btn, 0, 0)
        # grid2.addWidget(self.copytool_btn, 0, 1)
        grid0.addWidget(self.deltool_btn, 0, 2)

        grid0.addWidget(step1_lbl, 2, 0)
        grid0.addWidget(self.soldergeo_btn, 2, 2)

        ## Form Layout
        geo_form_layout = QtWidgets.QFormLayout()
        self.layout.addLayout(geo_form_layout)

        ## Geometry Object to be used for solderpaste dispensing
        self.geo_obj_combo = QtWidgets.QComboBox()
        self.geo_obj_combo.setModel(self.app.collection)
        self.geo_obj_combo.setRootModelIndex(self.app.collection.index(2, 0, QtCore.QModelIndex()))
        self.geo_obj_combo.setCurrentIndex(1)

        self.geo_object_label = QtWidgets.QLabel("Geometry:")
        self.geo_object_label.setToolTip(
            "Geometry Solder paste object.\n"
            "In order to enable the GCode generation section,\n"
            "the name of the object has to end in:\n"
            "'_solderpaste' as a protection."
        )
        geo_form_layout.addRow(self.geo_object_label, self.geo_obj_combo)

        self.gcode_frame = QtWidgets.QFrame()
        self.gcode_frame.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.gcode_frame)
        self.gcode_box = QtWidgets.QVBoxLayout()
        self.gcode_box.setContentsMargins(0, 0, 0, 0)
        self.gcode_frame.setLayout(self.gcode_box)

        ## Form Layout
        form_layout = QtWidgets.QFormLayout()
        self.gcode_box.addLayout(form_layout)

        # Z dispense start
        self.z_start_entry = FCEntry()
        self.z_start_label = QtWidgets.QLabel("Z Dispense Start:")
        self.z_start_label.setToolTip(
            "The height (Z) when solder paste dispensing starts."
        )
        form_layout.addRow(self.z_start_label, self.z_start_entry)

        # Z dispense
        self.z_dispense_entry = FCEntry()
        self.z_dispense_label = QtWidgets.QLabel("Z Dispense:")
        self.z_dispense_label.setToolTip(
            "The height (Z) when doing solder paste dispensing."

        )
        form_layout.addRow(self.z_dispense_label, self.z_dispense_entry)

        # Z dispense stop
        self.z_stop_entry = FCEntry()
        self.z_stop_label = QtWidgets.QLabel("Z Dispense Stop:")
        self.z_stop_label.setToolTip(
            "The height (Z) when solder paste dispensing stops."
        )
        form_layout.addRow(self.z_stop_label, self.z_stop_entry)

        # Z travel
        self.z_travel_entry = FCEntry()
        self.z_travel_label = QtWidgets.QLabel("Z Travel:")
        self.z_travel_label.setToolTip(
            "The height (Z) for travel between pads\n"
            "(without dispensing solder paste)."
        )
        form_layout.addRow(self.z_travel_label, self.z_travel_entry)

        # Feedrate X-Y
        self.frxy_entry = FCEntry()
        self.frxy_label = QtWidgets.QLabel("Feedrate X-Y:")
        self.frxy_label.setToolTip(
            "Feedrate (speed) while moving on the X-Y plane."
        )
        form_layout.addRow(self.frxy_label, self.frxy_entry)

        # Feedrate Z
        self.frz_entry = FCEntry()
        self.frz_label = QtWidgets.QLabel("Feedrate Z:")
        self.frz_label.setToolTip(
            "Feedrate (speed) while moving vertically\n"
            "(on Z plane)."
        )
        form_layout.addRow(self.frz_label, self.frz_entry)

        # Spindle Speed Forward
        self.speedfwd_entry = FCEntry()
        self.speedfwd_label = QtWidgets.QLabel("Spindle Speed FWD:")
        self.speedfwd_label.setToolTip(
            "The dispenser speed while pushing solder paste\n"
            "through the dispenser nozzle."
        )
        form_layout.addRow(self.speedfwd_label, self.speedfwd_entry)

        # Dwell Forward
        self.dwellfwd_entry = FCEntry()
        self.dwellfwd_label = QtWidgets.QLabel("Dwell FWD:")
        self.dwellfwd_label.setToolTip(
            "Pause after solder dispensing."
        )
        form_layout.addRow(self.dwellfwd_label, self.dwellfwd_entry)

        # Spindle Speed Reverse
        self.speedrev_entry = FCEntry()
        self.speedrev_label = QtWidgets.QLabel("Spindle Speed REV:")
        self.speedrev_label.setToolTip(
            "The dispenser speed while retracting solder paste\n"
            "through the dispenser nozzle."
        )
        form_layout.addRow(self.speedrev_label, self.speedrev_entry)

        # Dwell Reverse
        self.dwellrev_entry = FCEntry()
        self.dwellrev_label = QtWidgets.QLabel("Dwell REV:")
        self.dwellrev_label.setToolTip(
            "Pause after solder paste dispenser retracted,\n"
            "to allow pressure equilibrium."
        )
        form_layout.addRow(self.dwellrev_label, self.dwellrev_entry)

        # Postprocessors
        pp_label = QtWidgets.QLabel('PostProcessors:')
        pp_label.setToolTip(
            "Files that control the GCode generation."
        )

        self.pp_combo = FCComboBox()
        self.pp_combo.setStyleSheet('background-color: rgb(255,255,255)')
        form_layout.addRow(pp_label, self.pp_combo)

        ## Buttons
        grid1 = QtWidgets.QGridLayout()
        self.gcode_box.addLayout(grid1)

        self.solder_gcode_btn = QtWidgets.QPushButton("Generate GCode")
        self.solder_gcode_btn.setToolTip(
            "Generate GCode for Solder Paste dispensing\n"
            "on PCB pads."
        )

        step2_lbl = QtWidgets.QLabel("<b>STEP 2:</b>")
        step2_lbl.setToolTip(
            "Second step is to select a solder paste dispensing geometry,\n"
            "set the CAM parameters and then generate a CNCJob object which\n"
            "will pe painted on canvas in blue color."
        )

        grid1.addWidget(step2_lbl, 0, 0)
        grid1.addWidget(self.solder_gcode_btn, 0, 2)

        ## Form Layout
        cnc_form_layout = QtWidgets.QFormLayout()
        self.gcode_box.addLayout(cnc_form_layout)

        ## Gerber Object to be used for solderpaste dispensing
        self.cnc_obj_combo = QtWidgets.QComboBox()
        self.cnc_obj_combo.setModel(self.app.collection)
        self.cnc_obj_combo.setRootModelIndex(self.app.collection.index(3, 0, QtCore.QModelIndex()))
        self.cnc_obj_combo.setCurrentIndex(1)

        self.cnc_object_label = QtWidgets.QLabel("CNCJob:    ")
        self.cnc_object_label.setToolTip(
            "CNCJob Solder paste object.\n"
            "In order to enable the GCode save section,\n"
            "the name of the object has to end in:\n"
            "'_solderpaste' as a protection."
        )
        cnc_form_layout.addRow(self.cnc_object_label, self.cnc_obj_combo)

        self.save_gcode_frame = QtWidgets.QFrame()
        self.save_gcode_frame.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.save_gcode_frame)
        self.save_gcode_box = QtWidgets.QVBoxLayout()
        self.save_gcode_box.setContentsMargins(0, 0, 0, 0)
        self.save_gcode_frame.setLayout(self.save_gcode_box)


        ## Buttons
        grid2 = QtWidgets.QGridLayout()
        self.save_gcode_box.addLayout(grid2)

        self.solder_gcode_view_btn = QtWidgets.QPushButton("View GCode")
        self.solder_gcode_view_btn.setToolTip(
            "View the generated GCode for Solder Paste dispensing\n"
            "on PCB pads."
        )

        self.solder_gcode_save_btn = QtWidgets.QPushButton("Save GCode")
        self.solder_gcode_save_btn.setToolTip(
            "Save the generated GCode for Solder Paste dispensing\n"
            "on PCB pads, to a file."
        )

        step3_lbl = QtWidgets.QLabel("<b>STEP 3:</b>")
        step3_lbl.setToolTip(
            "Third step (and last) is to select a CNCJob made from \n"
            "a solder paste dispensing geometry, and then view/save it's GCode."
        )

        grid2.addWidget(step3_lbl, 0, 0)
        grid2.addWidget(self.solder_gcode_view_btn, 0, 2)
        grid2.addWidget(self.solder_gcode_save_btn, 1, 2)

        self.layout.addStretch()

        # self.gcode_frame.setDisabled(True)
        # self.save_gcode_frame.setDisabled(True)

        self.tools = {}
        self.tooluid = 0

        ## Signals
        self.addtool_btn.clicked.connect(self.on_tool_add)
        self.deltool_btn.clicked.connect(self.on_tool_delete)
        self.soldergeo_btn.clicked.connect(self.on_create_geo)
        self.solder_gcode_btn.clicked.connect(self.on_create_gcode)
        self.solder_gcode_view_btn.clicked.connect(self.on_view_gcode)
        self.solder_gcode_save_btn.clicked.connect(self.on_save_gcode)

        self.geo_obj_combo.currentIndexChanged.connect(self.on_geo_select)

        self.cnc_obj_combo.currentIndexChanged.connect(self.on_cncjob_select)

    def run(self):
        self.app.report_usage("ToolSolderPaste()")

        FlatCAMTool.run(self)
        self.set_tool_ui()

        # if the splitter us hidden, display it
        if self.app.ui.splitter.sizes()[0] == 0:
            self.app.ui.splitter.setSizes([1, 1])

        self.build_ui()
        self.app.ui.notebook.setTabText(2, "SolderPaste Tool")

    def install(self, icon=None, separator=None, **kwargs):
        FlatCAMTool.install(self, icon, separator, shortcut='ALT+K', **kwargs)

    def set_tool_ui(self):

        if self.app.defaults["tools_solderpaste_new"]:
            self.addtool_entry.set_value(self.app.defaults["tools_solderpaste_new"])
        else:
            self.addtool_entry.set_value(0.0)

        if self.app.defaults["tools_solderpaste_z_start"]:
            self.z_start_entry.set_value(self.app.defaults["tools_solderpaste_z_start"])
        else:
            self.z_start_entry.set_value(0.0)

        if self.app.defaults["tools_solderpaste_z_dispense"]:
            self.z_dispense_entry.set_value(self.app.defaults["tools_solderpaste_z_dispense"])
        else:
            self.z_dispense_entry.set_value(0.0)

        if self.app.defaults["tools_solderpaste_z_stop"]:
            self.z_stop_entry.set_value(self.app.defaults["tools_solderpaste_z_stop"])
        else:
            self.z_stop_entry.set_value(1.0)

        if self.app.defaults["tools_solderpaste_z_travel"]:
            self.z_travel_entry.set_value(self.app.defaults["tools_solderpaste_z_travel"])
        else:
            self.z_travel_entry.set_value(1.0)

        if self.app.defaults["tools_solderpaste_frxy"]:
            self.frxy_entry.set_value(self.app.defaults["tools_solderpaste_frxy"])
        else:
            self.frxy_entry.set_value(True)

        if self.app.defaults["tools_solderpaste_frz"]:
            self.frz_entry.set_value(self.app.defaults["tools_solderpaste_frz"])
        else:
            self.frz_entry.set_value(True)

        if self.app.defaults["tools_solderpaste_speedfwd"]:
            self.speedfwd_entry.set_value(self.app.defaults["tools_solderpaste_speedfwd"])
        else:
            self.speedfwd_entry.set_value(0.0)

        if self.app.defaults["tools_solderpaste_dwellfwd"]:
            self.dwellfwd_entry.set_value(self.app.defaults["tools_solderpaste_dwellfwd"])
        else:
            self.dwellfwd_entry.set_value(0.0)

        if self.app.defaults["tools_solderpaste_speedrev"]:
            self.speedrev_entry.set_value(self.app.defaults["tools_solderpaste_speedrev"])
        else:
            self.speedrev_entry.set_value(False)

        if self.app.defaults["tools_solderpaste_dwellrev"]:
            self.dwellrev_entry.set_value(self.app.defaults["tools_solderpaste_dwellrev"])
        else:
            self.dwellrev_entry.set_value((0, 0))

        if self.app.defaults["tools_solderpaste_pp"]:
            self.pp_combo.set_value(self.app.defaults["tools_solderpaste_pp"])
        else:
            self.pp_combo.set_value('Paste_1')

        self.tools_table.setupContextMenu()
        self.tools_table.addContextMenu(
            "Add", lambda: self.on_tool_add(dia=None, muted=None), icon=QtGui.QIcon("share/plus16.png"))
        self.tools_table.addContextMenu(
            "Delete", lambda:
            self.on_tool_delete(rows_to_delete=None, all=None), icon=QtGui.QIcon("share/delete32.png"))

        try:
            dias = [float(eval(dia)) for dia in self.app.defaults["tools_solderpaste_tools"].split(",")]
        except:
            log.error("At least one Nozzle tool diameter needed. "
                      "Verify in Edit -> Preferences -> TOOLS -> Solder Paste Tools.")
            return

        self.tooluid = 0

        self.tools.clear()
        for tool_dia in dias:
            self.tooluid += 1
            self.tools.update({
                int(self.tooluid): {
                    'tooldia': float('%.4f' % tool_dia),
                    'solid_geometry': []
                }
            })

        self.name = ""
        self.obj = None

        self.units = self.app.general_options_form.general_app_group.units_radio.get_value().upper()

        for name in list(self.app.postprocessors.keys()):
            # populate only with postprocessor files that start with 'Paste_'
            if name.partition('_')[0] != 'Paste':
                continue
            self.pp_combo.addItem(name)

        self.reset_fields()

    def build_ui(self):
        self.ui_disconnect()

        # updated units
        self.units = self.app.general_options_form.general_app_group.units_radio.get_value().upper()

        sorted_tools = []
        for k, v in self.tools.items():
            sorted_tools.append(float('%.4f' % float(v['tooldia'])))
        sorted_tools.sort(reverse=True)

        n = len(sorted_tools)
        self.tools_table.setRowCount(n)
        tool_id = 0

        for tool_sorted in sorted_tools:
            for tooluid_key, tooluid_value in self.tools.items():
                if float('%.4f' % tooluid_value['tooldia']) == tool_sorted:
                    tool_id += 1
                    id = QtWidgets.QTableWidgetItem('%d' % int(tool_id))
                    id.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                    row_no = tool_id - 1
                    self.tools_table.setItem(row_no, 0, id)  # Tool name/id

                    # Make sure that the drill diameter when in MM is with no more than 2 decimals
                    # There are no drill bits in MM with more than 3 decimals diameter
                    # For INCH the decimals should be no more than 3. There are no drills under 10mils
                    if self.units == 'MM':
                        dia = QtWidgets.QTableWidgetItem('%.2f' % tooluid_value['tooldia'])
                    else:
                        dia = QtWidgets.QTableWidgetItem('%.3f' % tooluid_value['tooldia'])

                    dia.setFlags(QtCore.Qt.ItemIsEnabled)

                    tool_uid_item = QtWidgets.QTableWidgetItem(str(int(tooluid_key)))

                    self.tools_table.setItem(row_no, 1, dia)  # Diameter

                    self.tools_table.setItem(row_no, 2, tool_uid_item)  # Tool unique ID

        # make the diameter column editable
        for row in range(tool_id):
            self.tools_table.item(row, 1).setFlags(
                QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

        # all the tools are selected by default
        self.tools_table.selectColumn(0)
        #
        self.tools_table.resizeColumnsToContents()
        self.tools_table.resizeRowsToContents()

        vertical_header = self.tools_table.verticalHeader()
        vertical_header.hide()
        self.tools_table.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        horizontal_header = self.tools_table.horizontalHeader()
        horizontal_header.setMinimumSectionSize(10)
        horizontal_header.setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
        horizontal_header.resizeSection(0, 20)
        horizontal_header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)

        # self.tools_table.setSortingEnabled(True)
        # sort by tool diameter
        # self.tools_table.sortItems(1)

        self.tools_table.setMinimumHeight(self.tools_table.getHeight())
        self.tools_table.setMaximumHeight(self.tools_table.getHeight())

        self.ui_connect()

    def ui_connect(self):
        self.tools_table.itemChanged.connect(self.on_tool_edit)

    def ui_disconnect(self):
        try:
            # if connected, disconnect the signal from the slot on item_changed as it creates issues
            self.tools_table.itemChanged.disconnect(self.on_tool_edit)
        except:
            pass

    def on_tool_add(self, dia=None, muted=None):

        self.ui_disconnect()

        if dia:
            tool_dia = dia
        else:
            try:
                tool_dia = float(self.addtool_entry.get_value())
            except ValueError:
                # try to convert comma to decimal point. if it's still not working error message and return
                try:
                    tool_dia = float(self.addtool_entry.get_value().replace(',', '.'))
                except ValueError:
                    self.app.inform.emit("[ERROR_NOTCL]Wrong value format entered, "
                                         "use a number.")
                    return
            if tool_dia is None:
                self.build_ui()
                self.app.inform.emit("[WARNING_NOTCL] Please enter a tool diameter to add, in Float format.")
                return

        if tool_dia == 0:
            self.app.inform.emit("[WARNING_NOTCL] Please enter a tool diameter with non-zero value, in Float format.")
            return

        # construct a list of all 'tooluid' in the self.tools
        tool_uid_list = []
        for tooluid_key in self.tools:
            tool_uid_item = int(tooluid_key)
            tool_uid_list.append(tool_uid_item)

        # find maximum from the temp_uid, add 1 and this is the new 'tooluid'
        if not tool_uid_list:
            max_uid = 0
        else:
            max_uid = max(tool_uid_list)
        self.tooluid = int(max_uid + 1)

        tool_dias = []
        for k, v in self.tools.items():
            for tool_v in v.keys():
                if tool_v == 'tooldia':
                    tool_dias.append(float('%.4f' % v[tool_v]))

        if float('%.4f' % tool_dia) in tool_dias:
            if muted is None:
                self.app.inform.emit("[WARNING_NOTCL]Adding Nozzle tool cancelled. Tool already in Tool Table.")
            self.tools_table.itemChanged.connect(self.on_tool_edit)
            return
        else:
            if muted is None:
                self.app.inform.emit("[success] New Nozzle tool added to Tool Table.")
            self.tools.update({
                int(self.tooluid): {
                    'tooldia': float('%.4f' % tool_dia),
                    'solid_geometry': []
                }
            })

        self.build_ui()

    def on_tool_edit(self):
        self.ui_disconnect()

        tool_dias = []
        for k, v in self.tools.items():
            for tool_v in v.keys():
                if tool_v == 'tooldia':
                    tool_dias.append(float('%.4f' % v[tool_v]))

        for row in range(self.tools_table.rowCount()):

            try:
                new_tool_dia = float(self.tools_table.item(row, 1).text())
            except ValueError:
                # try to convert comma to decimal point. if it's still not working error message and return
                try:
                    new_tool_dia = float(self.tools_table.item(row, 1).text().replace(',', '.'))
                except ValueError:
                    self.app.inform.emit("[ERROR_NOTCL]Wrong value format entered, "
                                         "use a number.")
                    return

            tooluid = int(self.tools_table.item(row, 2).text())

            # identify the tool that was edited and get it's tooluid
            if new_tool_dia not in tool_dias:
                self.tools[tooluid]['tooldia'] = new_tool_dia
                self.app.inform.emit("[success] Nozzle tool from Tool Table was edited.")
                self.build_ui()
                return
            else:
                # identify the old tool_dia and restore the text in tool table
                for k, v in self.tools.items():
                    if k == tooluid:
                        old_tool_dia = v['tooldia']
                        break
                restore_dia_item = self.tools_table.item(row, 1)
                restore_dia_item.setText(str(old_tool_dia))
                self.app.inform.emit("[WARNING_NOTCL] Edit cancelled. New diameter value is already in the Tool Table.")
        self.build_ui()

    def on_tool_delete(self, rows_to_delete=None, all=None):
        self.ui_disconnect()

        deleted_tools_list = []

        if all:
            self.tools.clear()
            self.build_ui()
            return

        if rows_to_delete:
            try:
                for row in rows_to_delete:
                    tooluid_del = int(self.tools_table.item(row, 2).text())
                    deleted_tools_list.append(tooluid_del)
            except TypeError:
                deleted_tools_list.append(rows_to_delete)

            for t in deleted_tools_list:
                self.tools.pop(t, None)
            self.build_ui()
            return

        try:
            if self.tools_table.selectedItems():
                for row_sel in self.tools_table.selectedItems():
                    row = row_sel.row()
                    if row < 0:
                        continue
                    tooluid_del = int(self.tools_table.item(row, 2).text())
                    deleted_tools_list.append(tooluid_del)

                for t in deleted_tools_list:
                    self.tools.pop(t, None)

        except AttributeError:
            self.app.inform.emit("[WARNING_NOTCL] Delete failed. Select a Nozzle tool to delete.")
            return
        except Exception as e:
            log.debug(str(e))

        self.app.inform.emit("[success] Nozzle tool(s) deleted from Tool Table.")
        self.build_ui()

    def on_geo_select(self):
        # if self.geo_obj_combo.currentText().rpartition('_')[2] == 'solderpaste':
        #     self.gcode_frame.setDisabled(False)
        # else:
        #     self.gcode_frame.setDisabled(True)
        pass

    def on_cncjob_select(self):
        # if self.cnc_obj_combo.currentText().rpartition('_')[2] == 'solderpaste':
        #     self.save_gcode_frame.setDisabled(False)
        # else:
        #     self.save_gcode_frame.setDisabled(True)
        pass

    @staticmethod
    def distance(pt1, pt2):
        return sqrt((pt1[0] - pt2[0]) ** 2 + (pt1[1] - pt2[1]) ** 2)

    def on_create_geo(self):
        proc = self.app.proc_container.new("Creating Solder Paste dispensing geometry.")

        name = self.obj_combo.currentText()
        if name == '':
            self.app.inform.emit("[WARNING_NOTCL] No SolderPaste mask Gerber object loaded.")
            return

        obj = self.app.collection.get_by_name(name)

        if type(obj.solid_geometry) is not list and type(obj.solid_geometry) is not MultiPolygon:
            obj.solid_geometry = [obj.solid_geometry]

        # Sort tools in descending order
        sorted_tools = []
        for k, v in self.tools.items():
            # make sure that the tools diameter is more than zero and not zero
            if float(v['tooldia']) > 0:
                sorted_tools.append(float('%.4f' % float(v['tooldia'])))
        sorted_tools.sort(reverse=True)

        def geo_init(geo_obj, app_obj):
            geo_obj.solid_geometry = []
            geo_obj.tools = {}
            geo_obj.multigeo = True
            geo_obj.multitool = True
            geo_obj.tools = {}

            def solder_line(p, offset):

                xmin, ymin, xmax, ymax = p.bounds

                min = [xmin, ymin]
                max = [xmax, ymax]
                min_r = [xmin, ymax]
                max_r = [xmax, ymin]

                diagonal_1 = LineString([min, max])
                diagonal_2 = LineString([min_r, max_r])
                round_diag_1 = round(diagonal_1.intersection(p).length, 2)
                round_diag_2 = round(diagonal_2.intersection(p).length, 2)

                if round_diag_1 == round_diag_2:
                    l = distance((xmin, ymin), (xmax, ymin))
                    h = distance((xmin, ymin), (xmin, ymax))
                    if offset >= l /2 or offset >= h / 2:
                        return "fail"
                    if l > h:
                        h_half = h / 2
                        start = [xmin, (ymin + h_half)]
                        stop = [(xmin + l), (ymin + h_half)]
                    else:
                        l_half = l / 2
                        start = [(xmin + l_half), ymin]
                        stop = [(xmin + l_half), (ymin + h)]
                    geo = LineString([start, stop])
                elif round_diag_1 > round_diag_2:
                    geo = diagonal_1.intersection(p)
                else:
                    geo = diagonal_2.intersection(p)

                offseted_poly = p.buffer(-offset)
                geo = geo.intersection(offseted_poly)
                return geo

            work_geo = obj.solid_geometry
            rest_geo = []
            tooluid = 1

            if not sorted_tools:
                self.app.inform.emit("[WARNING_NOTCL] No Nozzle tools in the tool table.")
                return 'fail'

            for tool in sorted_tools:

                offset = tool / 2

                for uid, v in self.tools.items():
                    if float('%.4f' % float(v['tooldia'])) == tool:
                        tooluid = int(uid)
                        break

                for g in work_geo:
                    if type(g) == MultiPolygon:
                        for poly in g:
                            geom = solder_line(poly, offset=offset)
                            if geom != 'fail':
                                try:
                                    geo_obj.tools[tooluid]['solid_geometry'].append(geom)
                                except KeyError:
                                    geo_obj.tools[tooluid] = {}
                                    geo_obj.tools[tooluid]['solid_geometry'] = []
                                    geo_obj.tools[tooluid]['solid_geometry'].append(geom)
                                geo_obj.tools[tooluid]['tooldia'] = tool
                                geo_obj.tools[tooluid]['offset'] = 'Path'
                                geo_obj.tools[tooluid]['offset_value'] = 0.0
                                geo_obj.tools[tooluid]['type'] = ' '
                                geo_obj.tools[tooluid]['tool_type'] = ' '
                                geo_obj.tools[tooluid]['data'] = {}
                            else:
                                rest_geo.append(poly)
                    elif type(g) == Polygon:
                        geom = solder_line(g, offset=offset)
                        if geom != 'fail':
                            try:
                                geo_obj.tools[tooluid]['solid_geometry'].append(geom)
                            except KeyError:
                                geo_obj.tools[tooluid] = {}
                                geo_obj.tools[tooluid]['solid_geometry'] = []
                                geo_obj.tools[tooluid]['solid_geometry'].append(geom)
                            geo_obj.tools[tooluid]['tooldia'] = tool
                            geo_obj.tools[tooluid]['offset'] = 'Path'
                            geo_obj.tools[tooluid]['offset_value'] = 0.0
                            geo_obj.tools[tooluid]['type'] = ' '
                            geo_obj.tools[tooluid]['tool_type'] = ' '
                            geo_obj.tools[tooluid]['data'] = {}
                        else:
                            rest_geo.append(g)

                work_geo = deepcopy(rest_geo)
                rest_geo[:] = []

                if not work_geo:
                    app_obj.inform.emit("[success] Solder Paste geometry generated successfully...")
                    return

            # if we still have geometry not processed at the end of the tools then we failed
            # some or all the pads are not covered with solder paste
            if rest_geo:
                app_obj.inform.emit("[WARNING_NOTCL] Some or all pads have no solder "
                                    "due of inadequate nozzle diameters...")
                return 'fail'

        def job_thread(app_obj):
            try:
                app_obj.new_object("geometry", name + "_solderpaste", geo_init)
            except Exception as e:
                proc.done()
                traceback.print_stack()
                return
            proc.done()

        self.app.inform.emit("Generating Solder Paste dispensing geometry...")
        # Promise object with the new name
        self.app.collection.promise(name)

        # Background
        self.app.worker_task.emit({'fcn': job_thread, 'params': [self.app]})
        # self.app.ui.notebook.setCurrentWidget(self.app.ui.project_tab)

    def on_view_gcode(self):
        # add the tab if it was closed
        self.app.ui.plot_tab_area.addTab(self.app.ui.cncjob_tab, "Code Editor")

        # Switch plot_area to CNCJob tab
        self.app.ui.plot_tab_area.setCurrentWidget(self.app.ui.cncjob_tab)

        name = self.cnc_obj_combo.currentText()
        obj = self.app.collection.get_by_name(name)

        # then append the text from GCode to the text editor
        try:
            file = StringIO(obj.gcode)
        except:
            self.app.inform.emit("[ERROR_NOTCL] No Gcode in the object...")
            return

        try:
            for line in file:
                proc_line = str(line).strip('\n')
                self.app.ui.code_editor.append(proc_line)
        except Exception as e:
            log.debug('ToolSolderPaste.on_view_gcode() -->%s' % str(e))
            self.app.inform.emit('[ERROR]ToolSolderPaste.on_view_gcode() -->%s' % str(e))
            return

        self.app.ui.code_editor.moveCursor(QtGui.QTextCursor.Start)

        self.app.handleTextChanged()
        self.app.ui.show()

    def on_save_gcode(self):
        time_str = "{:%A, %d %B %Y at %H:%M}".format(datetime.now())
        name = self.cnc_obj_combo.currentText()
        obj = self.app.collection.get_by_name(name)

        _filter_ = "G-Code Files (*.nc);;G-Code Files (*.txt);;G-Code Files (*.tap);;G-Code Files (*.cnc);;" \
                   "G-Code Files (*.g-code);;All Files (*.*)"

        try:
            dir_file_to_save = self.app.get_last_save_folder() + '/' + str(name)
            filename, _ = QtWidgets.QFileDialog.getSaveFileName(
                caption="Export GCode ...",
                directory=dir_file_to_save,
                filter=_filter_
            )
        except TypeError:
            filename, _ = QtWidgets.QFileDialog.getSaveFileName(caption="Export Machine Code ...", filter=_filter_)

        if filename == '':
            self.app.inform.emit("[WARNING_NOTCL]Export Machine Code cancelled ...")
            return

        gcode = '(G-CODE GENERATED BY FLATCAM v%s - www.flatcam.org - Version Date: %s)\n' % \
                (str(self.app.version), str(self.app.version_date)) + '\n'

        gcode += '(Name: ' + str(name) + ')\n'
        gcode += '(Type: ' + "G-code from " + str(obj.options['type']) + " for Solder Paste dispenser" + ')\n'

        # if str(p['options']['type']) == 'Excellon' or str(p['options']['type']) == 'Excellon Geometry':
        #     gcode += '(Tools in use: ' + str(p['options']['Tools_in_use']) + ')\n'

        gcode += '(Units: ' + self.units.upper() + ')\n' + "\n"
        gcode += '(Created on ' + time_str + ')\n' + '\n'

        gcode += obj.gcode
        lines = StringIO(gcode)

        ## Write
        if filename is not None:
            try:
                with open(filename, 'w') as f:
                    for line in lines:
                        f.write(line)
            except FileNotFoundError:
                self.app.inform.emit("[WARNING_NOTCL] No such file or directory")
                return

        self.app.file_saved.emit("gcode", filename)
        self.app.inform.emit("[success] Solder paste dispenser GCode file saved to: %s" % filename)

    def on_create_gcode(self, use_thread=True):
        """
                Creates a multi-tool CNCJob out of this Geometry object.
                The actual work is done by the target FlatCAMCNCjob object's
                `generate_from_geometry_2()` method.

                :param z_cut: Cut depth (negative)
                :param z_move: Hight of the tool when travelling (not cutting)
                :param feedrate: Feed rate while cutting on X - Y plane
                :param feedrate_z: Feed rate while cutting on Z plane
                :param feedrate_rapid: Feed rate while moving with rapids
                :param tooldia: Tool diameter
                :param outname: Name of the new object
                :param spindlespeed: Spindle speed (RPM)
                :param ppname_g Name of the postprocessor
                :return: None
                """

        name = self.obj_combo.currentText()
        obj = self.app.collection.get_by_name(name)

        offset_str = ''
        multitool_gcode = ''

        # use the name of the first tool selected in self.geo_tools_table which has the diameter passed as tool_dia
        outname = "%s_%s" % (name, 'cnc_solderpaste')

        try:
            xmin = obj.options['xmin']
            ymin = obj.options['ymin']
            xmax = obj.options['xmax']
            ymax = obj.options['ymax']
        except Exception as e:
            log.debug("FlatCAMObj.FlatCAMGeometry.mtool_gen_cncjob() --> %s\n" % str(e))
            msg = "[ERROR] An internal error has ocurred. See shell.\n"
            msg += 'FlatCAMObj.FlatCAMGeometry.mtool_gen_cncjob() --> %s' % str(e)
            msg += traceback.format_exc()
            self.app.inform.emit(msg)
            return


        # Object initialization function for app.new_object()
        # RUNNING ON SEPARATE THREAD!
        def job_init_multi_geometry(job_obj, app_obj):
            assert isinstance(job_obj, FlatCAMCNCjob), \
                "Initializer expected a FlatCAMCNCjob, got %s" % type(job_obj)

            # count the tools
            tool_cnt = 0
            dia_cnc_dict = {}
            current_uid = int(1)

            # this turn on the FlatCAMCNCJob plot for multiple tools
            job_obj.multitool = True
            job_obj.multigeo = True
            job_obj.cnc_tools.clear()

            job_obj.options['xmin'] = xmin
            job_obj.options['ymin'] = ymin
            job_obj.options['xmax'] = xmax
            job_obj.options['ymax'] = ymax


            try:
                job_obj.feedrate_probe = float(self.options["feedrate_probe"])
            except ValueError:
                # try to convert comma to decimal point. if it's still not working error message and return
                try:
                    job_obj.feedrate_rapid = float(self.options["feedrate_probe"].replace(',', '.'))
                except ValueError:
                    self.app.inform.emit(
                        '[ERROR_NOTCL]Wrong value format for self.defaults["feedrate_probe"] '
                        'or self.options["feedrate_probe"]')

            # make sure that trying to make a CNCJob from an empty file is not creating an app crash
            if not self.solid_geometry:
                a = 0
                for tooluid_key in self.tools:
                    if self.tools[tooluid_key]['solid_geometry'] is None:
                        a += 1
                if a == len(self.tools):
                    self.app.inform.emit('[ERROR_NOTCL]Cancelled. Empty file, it has no geometry...')
                    return 'fail'

            for tooluid_key in self.tools:
                tool_cnt += 1
                app_obj.progress.emit(20)

                # find the tool_dia associated with the tooluid_key
                tool_dia = self.sel_tools[tooluid_key]['tooldia']

                # search in the self.tools for the sel_tool_dia and when found see what tooluid has
                # on the found tooluid in self.tools we also have the solid_geometry that interest us
                for k, v in self.tools.items():
                    if float('%.4f' % float(v['tooldia'])) == float('%.4f' % float(tool_dia)):
                        current_uid = int(k)
                        break

                for diadict_key, diadict_value in self.sel_tools[tooluid_key].items():
                    if diadict_key == 'tooldia':
                        tooldia_val = float('%.4f' % float(diadict_value))
                        dia_cnc_dict.update({
                            diadict_key: tooldia_val
                        })
                    if diadict_key == 'offset':
                        dia_cnc_dict.update({
                            diadict_key: ''
                        })

                    if diadict_key == 'type':
                        dia_cnc_dict.update({
                            diadict_key: ''
                        })

                    if diadict_key == 'tool_type':
                        dia_cnc_dict.update({
                            diadict_key: ''
                        })

                    if diadict_key == 'data':
                        for data_key, data_value in diadict_value.items():
                            if data_key == "multidepth":
                                multidepth = data_value
                            if data_key == "depthperpass":
                                depthpercut = data_value

                            if data_key == "extracut":
                                extracut = data_value
                            if data_key == "startz":
                                startz = data_value
                            if data_key == "endz":
                                endz = data_value

                            if data_key == "toolchangez":
                                toolchangez = data_value
                            if data_key == "toolchangexy":
                                toolchangexy = data_value
                            if data_key == "toolchange":
                                toolchange = data_value

                            if data_key == "cutz":
                                z_cut = data_value
                            if data_key == "travelz":
                                z_move = data_value

                            if data_key == "feedrate":
                                feedrate = data_value
                            if data_key == "feedrate_z":
                                feedrate_z = data_value
                            if data_key == "feedrate_rapid":
                                feedrate_rapid = data_value

                            if data_key == "ppname_g":
                                pp_geometry_name = data_value

                            if data_key == "spindlespeed":
                                spindlespeed = data_value
                            if data_key == "dwell":
                                dwell = data_value
                            if data_key == "dwelltime":
                                dwelltime = data_value

                        datadict = copy.deepcopy(diadict_value)
                        dia_cnc_dict.update({
                            diadict_key: datadict
                        })

                job_obj.coords_decimals = self.app.defaults["cncjob_coords_decimals"]
                job_obj.fr_decimals = self.app.defaults["cncjob_fr_decimals"]

                # Propagate options
                job_obj.options["tooldia"] = tooldia_val
                job_obj.options['type'] = 'Geometry'
                job_obj.options['tool_dia'] = tooldia_val

                app_obj.progress.emit(40)

                tool_solid_geometry = self.tools[current_uid]['solid_geometry']
                res = job_obj.generate_from_multitool_geometry(
                    tool_solid_geometry, tooldia=tooldia_val, offset=0.0,
                    tolerance=0.0005, z_cut=z_cut, z_move=z_move,
                    feedrate=feedrate, feedrate_z=feedrate_z, feedrate_rapid=feedrate_rapid,
                    spindlespeed=spindlespeed, dwell=dwell, dwelltime=dwelltime,
                    multidepth=multidepth, depthpercut=depthpercut,
                    extracut=extracut, startz=startz, endz=endz,
                    toolchange=toolchange, toolchangez=toolchangez, toolchangexy=toolchangexy,
                    pp_geometry_name=pp_geometry_name,
                    tool_no=tool_cnt)

                if res == 'fail':
                    log.debug("FlatCAMGeometry.mtool_gen_cncjob() --> generate_from_geometry2() failed")
                    return 'fail'
                else:
                    dia_cnc_dict['gcode'] = res

                dia_cnc_dict['gcode_parsed'] = job_obj.gcode_parse()

                # TODO this serve for bounding box creation only; should be optimized
                dia_cnc_dict['solid_geometry'] = cascaded_union([geo['geom'] for geo in dia_cnc_dict['gcode_parsed']])

                # tell gcode_parse from which point to start drawing the lines depending on what kind of
                # object is the source of gcode
                job_obj.toolchange_xy_type = "geometry"

                app_obj.progress.emit(80)

                job_obj.cnc_tools.update({
                    tooluid_key: copy.deepcopy(dia_cnc_dict)
                })
                dia_cnc_dict.clear()

        if use_thread:
            # To be run in separate thread
            # The idea is that if there is a solid_geometry in the file "root" then most likely thare are no
            # separate solid_geometry in the self.tools dictionary
            def job_thread(app_obj):
                with self.app.proc_container.new("Generating CNC Code"):
                    if app_obj.new_object("cncjob", outname, job_init_multi_geometry) != 'fail':
                        app_obj.inform.emit("[success]ToolSolderPaste CNCjob created: %s" % outname)
                        app_obj.progress.emit(100)

            # Create a promise with the name
            self.app.collection.promise(outname)
            # Send to worker
            self.app.worker_task.emit({'fcn': job_thread, 'params': [self.app]})
        else:
            self.app.new_object("cncjob", outname, job_init_multi_geometry)

    def reset_fields(self):
        self.obj_combo.setRootModelIndex(self.app.collection.index(0, 0, QtCore.QModelIndex()))
        self.geo_obj_combo.setRootModelIndex(self.app.collection.index(2, 0, QtCore.QModelIndex()))
        self.cnc_obj_combo.setRootModelIndex(self.app.collection.index(3, 0, QtCore.QModelIndex()))
