import tkinter as tk
from tkinter import messagebox
import math
import os
from tkinter import ttk

# ============================================================
# GCAE SURVEYING SOFTWARE
# Full Traverse Module
# ============================================================

window = tk.Tk()
window.title("GCAE Surveying Software")
window.geometry("1400x820")
window.minsize(1100, 650)

# ============================================================
# LOGO
# ============================================================

logo_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "gcae_logo.png"
)

try:
    logo_image = tk.PhotoImage(file=logo_path)

    # Keep the original image if reasonably sized.
    # Tkinter PhotoImage cannot resize arbitrarily, so large logos
    # are simply displayed using the original image.
    logo_label = tk.Label(window, image=logo_image)
    logo_label.pack(pady=5)

except Exception:
    logo_label = tk.Label(
        window,
        text="GCAE",
        font=("Arial", 22, "bold")
    )
    logo_label.pack(pady=10)


# ============================================================
# TITLE
# ============================================================

tk.Label(
    window,
    text="GCAE SURVEYING SOFTWARE",
    font=("Arial", 24, "bold")
).pack(pady=8)


# ============================================================
# TRAVERSE
# ============================================================

traverse_window = None


def open_traverse():

    global traverse_window

    # Keep the traverse window alive when the user goes back to the main
    # window. Re-opening Traverse restores the same table and entered data.
    if traverse_window is not None and traverse_window.winfo_exists():
        traverse_window.deiconify()
        traverse_window.lift()
        traverse_window.focus_force()
        return

    calculation_history = []

    tw = tk.Toplevel(window)
    traverse_window = tw
    tw.title("GCAE - Traverse Computation")
    tw.geometry("1500x850")

    def go_back_without_losing_data():
        # Hide instead of destroy. Nothing entered in the table is lost.
        tw.withdraw()

    tw.protocol("WM_DELETE_WINDOW", go_back_without_losing_data)
    tw.minsize(1150, 650)

    # --------------------------------------------------------
    # HELPERS
    # --------------------------------------------------------

    def clear_widget(widget):
        if isinstance(widget, tk.Entry):
            widget.delete(0, tk.END)
        elif isinstance(widget, tk.Label):
            widget.config(text="")

    def set_entry(entry, value):
        entry.delete(0, tk.END)
        entry.insert(0, value)

    def dms_to_decimal(deg, minute, second):
        d = float(deg)
        m = float(minute)
        s = float(second)

        if d < 0 or m < 0 or s < 0:
            raise ValueError("DMS values cannot be negative.")

        if m >= 60 or s >= 60:
            raise ValueError("Minutes and seconds must be less than 60.")

        return d + m / 60.0 + s / 3600.0

    def decimal_to_dms(value):
        value %= 360.0

        degree = int(value)
        minutes_float = (value - degree) * 60.0
        minute = int(minutes_float)
        second = round((minutes_float - minute) * 60.0, 2)

        if second >= 60:
            second = 0.0
            minute += 1

        if minute >= 60:
            minute = 0
            degree += 1

        degree %= 360
        return degree, minute, second

    def fmt(value):
        return f"{value:.3f}"

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    tk.Label(
        tw,
        text="TRAVERSE COMPUTATION",
        font=("Arial", 21, "bold")
    ).pack(pady=8)

    # --------------------------------------------------------
    # CONTROL FRAME
    # --------------------------------------------------------

    controls = tk.Frame(tw, relief=tk.GROOVE, borderwidth=2)
    controls.pack(fill="x", padx=10, pady=5)

    tk.Label(
        controls,
        text="Number of Stations:",
        font=("Arial", 10, "bold")
    ).grid(row=0, column=0, padx=5, pady=5)

    station_count = tk.Entry(controls, width=8)
    station_count.grid(row=0, column=1, padx=5)

    tk.Button(
        controls,
        text="CREATE TABLE",
        width=16,
        command=lambda: create_table()
    ).grid(row=0, column=2, padx=8)

    tk.Button(
        controls,
        text="CALCULATE / UPDATE",
        width=19,
        command=lambda: calculate()
    ).grid(row=0, column=3, padx=8)

    tk.Button(
        controls,
        text="CLEAR CALCULATIONS",
        width=19,
        command=lambda: clear_calculations()
    ).grid(row=0, column=4, padx=8)

    tk.Button(
        controls,
        text="HISTORY",
        width=14,
        command=lambda: show_history()
    ).grid(row=0, column=6, padx=8)

    tk.Button(
        controls,
        text="BACK",
        width=10,
        command=go_back_without_losing_data
    ).grid(row=0, column=7, padx=8)

    tk.Button(
        controls,
        text="CLEAR ALL DATA",
        width=16,
        command=lambda: clear_all()
    ).grid(row=0, column=5, padx=8)

    # Starting coordinates
    tk.Label(
        controls,
        text="Start Northing (X):"
    ).grid(row=1, column=0, padx=5, pady=5)

    start_n = tk.Entry(controls, width=15)
    start_n.grid(row=1, column=1, padx=5)

    tk.Label(
        controls,
        text="Start Easting (Y):"
    ).grid(row=1, column=2, padx=5, pady=5)

    start_e = tk.Entry(controls, width=15)
    start_e.grid(row=1, column=3, padx=5)

    # Starting bearing
    tk.Label(
        controls,
        text="Starting Bearing DMS:"
    ).grid(row=1, column=4, padx=5)

    start_bd = tk.Entry(controls, width=6)
    start_bd.grid(row=1, column=5, sticky="w")

    start_bm = tk.Entry(controls, width=6)
    start_bm.grid(row=1, column=5, padx=(55, 0), sticky="w")

    start_bs = tk.Entry(controls, width=6)
    start_bs.grid(row=1, column=5, padx=(110, 0), sticky="w")

    tk.Label(
        controls,
        text="deg   min   sec",
        font=("Arial", 8)
    ).grid(row=2, column=5, sticky="w", padx=2)

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    status = tk.Label(
        tw,
        text="Enter number of stations and click CREATE TABLE.",
        anchor="w",
        font=("Arial", 10)
    )
    status.pack(fill="x", padx=10, pady=3)

    # --------------------------------------------------------
    # SCROLLABLE TABLE
    # --------------------------------------------------------

    outer = tk.Frame(tw)
    outer.pack(fill="both", expand=True, padx=10, pady=5)

    canvas = tk.Canvas(outer)
    ybar = tk.Scrollbar(
        outer, orient="vertical", command=canvas.yview
    )
    xbar = tk.Scrollbar(
        outer, orient="horizontal", command=canvas.xview
    )

    canvas.configure(
        yscrollcommand=ybar.set,
        xscrollcommand=xbar.set
    )

    ybar.pack(side="right", fill="y")
    xbar.pack(side="bottom", fill="x")
    canvas.pack(side="left", fill="both", expand=True)

    table = tk.Frame(canvas)
    canvas.create_window((0, 0), window=table, anchor="nw")

    table.bind(
        "<Configure>",
        lambda event: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    # --------------------------------------------------------
    # DATA STRUCTURES
    # --------------------------------------------------------

    station_rows = []
    leg_rows = []
    summary = {}

    # --------------------------------------------------------
    # TABLE HEADER
    # --------------------------------------------------------

    def create_headers():
        headers = [
            ("STATION", 14),
            ("ANGLE\nDEG", 8),
            ("MIN", 6),
            ("SEC", 6),
            ("ANGLE\nCOR", 9),
            ("BEARING\nDEG", 9),
            ("MIN", 6),
            ("SEC", 6),
            ("DISTANCE\nm", 12),
            ("ΔN\nm", 12),
            ("CORR N\nm", 11),
            ("ΔE\nm", 12),
            ("CORR E\nm", 11),
            ("NORTHING\nm", 15),
            ("EASTING\nm", 15),
            ("STATION", 14),
            ("AS", 8),
            ("MS", 8),
            ("REMARKS", 18)
        ]

        for col, (text, width) in enumerate(headers):
            tk.Label(
                table,
                text=text,
                width=width,
                height=2,
                relief="solid",
                borderwidth=1,
                font=("Arial", 8, "bold")
            ).grid(row=0, column=col, sticky="nsew")

    # --------------------------------------------------------
    # CREATE TABLE
    # --------------------------------------------------------

    def create_table():

        # Existing observations are deliberately cleared only
        # when the user explicitly presses CREATE TABLE again.
        for widget in table.winfo_children():
            widget.destroy()

        station_rows.clear()
        leg_rows.clear()
        summary.clear()

        try:
            n = int(station_count.get())
            if n < 2:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Invalid Input",
                "Number of stations must be at least 2."
            )
            return

        create_headers()

        # ----------------------------------------------
        # Each station gets a station row.
        # Each line between two stations gets a bearing row.
        # ----------------------------------------------

        row = 1

        for i in range(n):

            sr = {}

            sr["station"] = tk.Entry(table, width=14)
            sr["station"].grid(row=row, column=0)

            sr["angle_d"] = tk.Entry(table, width=8)
            sr["angle_d"].grid(row=row, column=1)

            sr["angle_m"] = tk.Entry(table, width=6)
            sr["angle_m"].grid(row=row, column=2)

            sr["angle_s"] = tk.Entry(table, width=6)
            sr["angle_s"].grid(row=row, column=3)

            sr["angle_cor"] = tk.Entry(table, width=9)
            sr["angle_cor"].grid(row=row, column=4)

            # Bearing/distance are intentionally blank on station row.
            for c in range(5, 13):
                tk.Label(
                    table,
                    text="",
                    width=10,
                    relief="solid",
                    borderwidth=1
                ).grid(row=row, column=c)

            sr["northing"] = tk.Entry(table, width=15)
            sr["northing"].grid(row=row, column=13)

            sr["easting"] = tk.Entry(table, width=15)
            sr["easting"].grid(row=row, column=14)

            sr["station2"] = tk.Entry(table, width=14)
            sr["station2"].grid(row=row, column=15)

            sr["as"] = tk.Entry(table, width=8)
            sr["as"].grid(row=row, column=16)

            sr["ms"] = tk.Entry(table, width=8)
            sr["ms"].grid(row=row, column=17)

            sr["remarks"] = tk.Entry(table, width=18)
            sr["remarks"].grid(row=row, column=18)

            station_rows.append(sr)
            row += 1

            # ------------------------------------------
            # Bearing row exists BETWEEN station i and i+1
            # ------------------------------------------

            if i < n - 1:

                lr = {}

                # Blank station/angle area
                for c, width in [
                    (0, 14), (1, 8), (2, 6), (3, 6), (4, 9)
                ]:
                    tk.Label(
                        table,
                        text="",
                        width=width,
                        relief="solid",
                        borderwidth=1
                    ).grid(row=row, column=c)

                # Bearing DEG/MIN/SEC
                lr["bearing_d"] = tk.Entry(table, width=9)
                lr["bearing_d"].grid(row=row, column=5)

                lr["bearing_m"] = tk.Entry(table, width=6)
                lr["bearing_m"].grid(row=row, column=6)

                lr["bearing_s"] = tk.Entry(table, width=6)
                lr["bearing_s"].grid(row=row, column=7)

                lr["distance"] = tk.Entry(table, width=12)
                lr["distance"].grid(row=row, column=8)

                # Calculated values
                lr["dn"] = tk.Label(
                    table, text="", width=12,
                    relief="solid", borderwidth=1
                )
                lr["dn"].grid(row=row, column=9)

                lr["corr_n"] = tk.Label(
                    table, text="", width=11,
                    relief="solid", borderwidth=1
                )
                lr["corr_n"].grid(row=row, column=10)

                lr["de"] = tk.Label(
                    table, text="", width=12,
                    relief="solid", borderwidth=1
                )
                lr["de"].grid(row=row, column=11)

                lr["corr_e"] = tk.Label(
                    table, text="", width=11,
                    relief="solid", borderwidth=1
                )
                lr["corr_e"].grid(row=row, column=12)

                for c in range(13, 19):
                    tk.Label(
                        table,
                        text="",
                        width=14,
                        relief="solid",
                        borderwidth=1
                    ).grid(row=row, column=c)

                leg_rows.append(lr)
                row += 1

        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        row += 1

        summary_names = [
            ("Stations", "stations"),
            ("Angular Misclosure (AS)", "angular"),
            ("Total Distance", "distance"),
            ("N Misclosure", "nmis"),
            ("E Misclosure", "emis"),
            ("Linear Misclosure (MS)", "linear"),
            ("Accuracy", "accuracy")
        ]

        for col, (name, key) in enumerate(summary_names):
            tk.Label(
                table,
                text=name,
                font=("Arial", 8, "bold"),
                relief="solid",
                borderwidth=1,
                width=15
            ).grid(row=row, column=col * 2, columnspan=2)

            summary[key] = tk.Label(
                table,
                text="",
                relief="solid",
                borderwidth=1,
                width=15
            )
            summary[key].grid(
                row=row + 1,
                column=col * 2,
                columnspan=2
            )

        status.config(
            text=(
                f"{n} stations created. "
                "Enter observations. You can edit them at any time."
            )
        )

    # --------------------------------------------------------
    # CLEAR CALCULATIONS ONLY
    # --------------------------------------------------------

    def clear_calculations():

        for sr in station_rows:
            sr["angle_cor"].delete(0, tk.END)

        for lr in leg_rows:
            for key in ("dn", "corr_n", "de", "corr_e"):
                lr[key].config(text="")

        for sr in station_rows:
            sr["northing"].delete(0, tk.END)
            sr["easting"].delete(0, tk.END)

        for key, label in summary.items():
            label.config(text="")

        status.config(
            text=(
                "Calculations cleared. "
                "Your station, angle, bearing and distance data remain."
            )
        )

    # --------------------------------------------------------
    # CLEAR EVERYTHING
    # --------------------------------------------------------

    def clear_all():

        answer = messagebox.askyesno(
            "Clear All Data",
            "This will remove all observations and calculations. Continue?"
        )

        if not answer:
            return

        for widget in table.winfo_children():
            widget.destroy()

        station_rows.clear()
        leg_rows.clear()
        summary.clear()

        status.config(
            text="All traverse data cleared."
        )

    # --------------------------------------------------------
    # CALCULATION HISTORY
    # --------------------------------------------------------

    def show_history():

        hw = tk.Toplevel(tw)
        hw.title("GCAE - Calculation History")
        hw.geometry("1100x600")
        hw.minsize(800, 450)

        tk.Label(
            hw,
            text="CALCULATED TRAVERSE HISTORY",
            font=("Arial", 18, "bold")
        ).pack(pady=10)

        frame = tk.Frame(hw)
        frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = (
            "No.",
            "Time",
            "Stations",
            "Total Distance",
            "N Misclosure",
            "E Misclosure",
            "Linear Misclosure",
            "Accuracy"
        )

        tree = ttk.Treeview(
            frame,
            columns=columns,
            show="headings"
        )

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=130, anchor="center")

        yscroll = tk.Scrollbar(
            frame,
            orient="vertical",
            command=tree.yview
        )
        tree.configure(yscrollcommand=yscroll.set)

        yscroll.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)

        def refresh():
            for item in tree.get_children():
                tree.delete(item)

            for i, record in enumerate(calculation_history, start=1):
                tree.insert(
                    "",
                    "end",
                    values=(
                        i,
                        record["time"],
                        record["stations"],
                        record["distance"],
                        record["nmis"],
                        record["emis"],
                        record["linear"],
                        record["accuracy"]
                    )
                )

        def show_selected():
            selected = tree.selection()

            if not selected:
                messagebox.showinfo(
                    "History",
                    "Select a calculation first."
                )
                return

            item = tree.item(selected[0])
            index = int(item["values"][0]) - 1

            if index < 0 or index >= len(calculation_history):
                return

            record = calculation_history[index]

            detail = tk.Toplevel(hw)
            detail.title("Calculation Details")
            detail.geometry("1000x650")

            text = tk.Text(
                detail,
                wrap="none",
                font=("Courier New", 10)
            )
            text.pack(
                fill="both",
                expand=True,
                padx=10,
                pady=10
            )

            text.insert("1.0", record["details"])
            text.config(state="disabled")

        buttons = tk.Frame(hw)
        buttons.pack(pady=8)

        tk.Button(
            buttons,
            text="VIEW SELECTED",
            width=18,
            command=show_selected
        ).pack(side="left", padx=5)

        tk.Button(
            buttons,
            text="REFRESH",
            width=12,
            command=refresh
        ).pack(side="left", padx=5)

        tk.Button(
            buttons,
            text="CLOSE",
            width=12,
            command=hw.destroy
        ).pack(side="left", padx=5)

        refresh()

    # --------------------------------------------------------
    # CALCULATE / UPDATE
    # --------------------------------------------------------

    def calculate():
        """Calculate without deleting user input.

        IMPORTANT DESIGN RULE:
        1. Validate ALL required inputs first.
        2. If anything is missing/invalid, show the error and keep
           every field exactly as the user entered it.
        3. Only after validation succeeds are calculated fields updated.
        """

        if not station_rows:
            messagebox.showwarning(
                "No Table",
                "First enter the number of stations and click CREATE TABLE."
            )
            return

        try:
            n = len(station_rows)

            # ----------------------------------------------
            # VALIDATION ONLY — NOTHING IS CHANGED HERE
            # ----------------------------------------------

            if not start_n.get().strip():
                start_n.focus_set()
                raise ValueError("Starting Northing is missing.")

            if not start_e.get().strip():
                start_e.focus_set()
                raise ValueError("Starting Easting is missing.")

            x0 = float(start_n.get())
            y0 = float(start_e.get())

            if not start_bd.get().strip():
                start_bd.focus_set()
                raise ValueError("Starting bearing degree is missing.")
            if not start_bm.get().strip():
                start_bm.focus_set()
                raise ValueError("Starting bearing minute is missing.")
            if not start_bs.get().strip():
                start_bs.focus_set()
                raise ValueError("Starting bearing second is missing.")

            start_bearing = dms_to_decimal(
                start_bd.get(), start_bm.get(), start_bs.get()
            )

            # ----------------------------------------------
            # ANGLES
            #
            # The first and last station are end/control points
            # in the layout used by GCAE. Therefore the actual
            # observed angles are the intermediate station rows.
            # This matches the paper-style table where the first
            # station and closing station can have blank angle cells.
            # ----------------------------------------------

            observed_angles = []
            angle_station_indexes = []

            for i in range(1, n - 1):
                sr = station_rows[i]

                for key, name in [
                    ("angle_d", "angle degree"),
                    ("angle_m", "angle minute"),
                    ("angle_s", "angle second")
                ]:
                    if not sr[key].get().strip():
                        sr[key].focus_set()
                        raise ValueError(
                            f"{name} is missing at station row {i + 1}."
                        )

                angle = dms_to_decimal(
                    sr["angle_d"].get(),
                    sr["angle_m"].get(),
                    sr["angle_s"].get()
                )
                observed_angles.append(angle)
                angle_station_indexes.append(i)

            # For a closed traverse, the theoretical angle sum uses
            # the number of observed angles, not the number of visual
            # station/control rows.
            angle_count = len(observed_angles)
            if angle_count < 1:
                raise ValueError(
                    "At least one observed angle is required between the first and last station."
                )

            # ----------------------------------------------
            # BEARING/DISTANCE VALIDATION
            #
            # Bearing is entered on the line between two stations.
            # All bearing rows remain editable.
            # ----------------------------------------------

            bearings = []

            for i, lr in enumerate(leg_rows):
                # First line can use the starting bearing entered
                # above. If the line cells are filled, they are used
                # as the explicit bearing observation.
                entered = all(
                    lr[k].get().strip()
                    for k in ("bearing_d", "bearing_m", "bearing_s")
                )

                if entered:
                    b = dms_to_decimal(
                        lr["bearing_d"].get(),
                        lr["bearing_m"].get(),
                        lr["bearing_s"].get()
                    )
                elif i == 0:
                    b = start_bearing
                else:
                    lr["bearing_d"].focus_set()
                    raise ValueError(
                        f"Bearing is missing between station row {i + 1} and station row {i + 2}."
                    )

                bearings.append(b)

            # Distance is required on every line.
            distances = []
            for i, lr in enumerate(leg_rows):
                if not lr["distance"].get().strip():
                    lr["distance"].focus_set()
                    raise ValueError(
                        f"Distance is missing between station row {i + 1} and station row {i + 2}."
                    )

                distance = float(lr["distance"].get())
                if distance < 0:
                    lr["distance"].focus_set()
                    raise ValueError(
                        f"Distance cannot be negative on line {i + 1}."
                    )
                distances.append(distance)

            # ----------------------------------------------
            # ALL INPUTS ARE VALID FROM HERE DOWN.
            # Only now do we update calculated fields.
            # ----------------------------------------------

            # Angular misclosure based on observed intermediate angles.
            # This preserves the editable observation fields.
            theoretical_sum = max(angle_count - 2, 0) * 180.0
            observed_sum = sum(observed_angles)
            # Angular misclosure:
            # AS = observed angle sum - theoretical angle sum.
            # The correction applied to each observed angle is the
            # equal-and-opposite value distributed over all observed angles.
            angular_misclosure = observed_sum - theoretical_sum
            angular_correction = (
                -angular_misclosure / angle_count
                if angle_count else 0.0
            )
            misclosure_seconds = angular_misclosure * 3600.0
            correction_seconds = angular_correction * 3600.0

            corrected_angles = []
            for idx, angle in zip(angle_station_indexes, observed_angles):
                corrected = angle + angular_correction
                corrected_angles.append(corrected)
                station_rows[idx]["angle_cor"].delete(0, tk.END)
                station_rows[idx]["angle_cor"].insert(
                    0, f"{correction_seconds:.2f}"
                )

            # ----------------------------------------------
            # BEARING PROPAGATION
            #
            # If a bearing is explicitly entered on a bearing row,
            # preserve it. Blank later bearings are derived from the
            # previous bearing + the corresponding corrected angle.
            # ----------------------------------------------

            for i, lr in enumerate(leg_rows):
                entered = all(
                    lr[k].get().strip()
                    for k in ("bearing_d", "bearing_m", "bearing_s")
                )

                if not entered and i > 0:
                    # The angle controlling the next bearing is the
                    # intermediate station immediately before that leg.
                    angle_index = i
                    if angle_index >= n - 1:
                        angle_index = n - 2
                    b = (bearings[i - 1] + corrected_angles[angle_index - 1]) % 360.0
                    d, m, sec = decimal_to_dms(b)
                    set_entry(lr["bearing_d"], d)
                    set_entry(lr["bearing_m"], m)
                    set_entry(lr["bearing_s"], f"{sec:.2f}")
                    bearings[i] = b

            # ----------------------------------------------
            # LATITUDES / DEPARTURES
            # ----------------------------------------------

            total_distance = sum(distances)
            if total_distance <= 0:
                raise ValueError("Total distance must be greater than zero.")

            sum_dn = 0.0
            sum_de = 0.0

            for i, lr in enumerate(leg_rows):
                distance = distances[i]
                rad = math.radians(bearings[i])

                dn = distance * math.cos(rad)
                de = distance * math.sin(rad)

                lr["dn"].config(text=fmt(dn))
                lr["de"].config(text=fmt(de))

                sum_dn += dn
                sum_de += de

            # ----------------------------------------------
            # BOWDITCH CORRECTIONS
            # ----------------------------------------------

            for i, lr in enumerate(leg_rows):
                distance = distances[i]

                corr_n = -sum_dn * distance / total_distance
                corr_e = -sum_de * distance / total_distance

                lr["corr_n"].config(text=fmt(corr_n))
                lr["corr_e"].config(text=fmt(corr_e))

            # ----------------------------------------------
            # COORDINATES
            # ----------------------------------------------

            current_n = x0
            current_e = y0

            set_entry(station_rows[0]["northing"], fmt(current_n))
            set_entry(station_rows[0]["easting"], fmt(current_e))
            set_entry(station_rows[0]["station2"], station_rows[0]["station"].get())

            for i, lr in enumerate(leg_rows):
                dn = float(lr["dn"].cget("text"))
                de = float(lr["de"].cget("text"))
                cn = float(lr["corr_n"].cget("text"))
                ce = float(lr["corr_e"].cget("text"))

                current_n += dn + cn
                current_e += de + ce

                next_station = station_rows[i + 1]
                set_entry(next_station["northing"], fmt(current_n))
                set_entry(next_station["easting"], fmt(current_e))
                set_entry(next_station["station2"], next_station["station"].get())

            # ----------------------------------------------
            # FINAL RESULTS
            # ----------------------------------------------

            linear_misclosure = math.sqrt(sum_dn ** 2 + sum_de ** 2)
            if linear_misclosure == 0:
                accuracy_text = "Perfect / Closed"
            else:
                accuracy = total_distance / linear_misclosure
                accuracy_text = f"1 : {accuracy:.0f}"

            summary["stations"].config(text=str(n))
            summary["angular"].config(
                text=f"AS = {misclosure_seconds:+.2f} sec | Corr = {correction_seconds:+.2f} sec/stn"
            )
            summary["distance"].config(text=f"{total_distance:.3f} m")
            summary["nmis"].config(text=f"{sum_dn:.3f} m")
            summary["emis"].config(text=f"{sum_de:.3f} m")
            summary["linear"].config(text=f"MS = {linear_misclosure:.3f} m")
            summary["accuracy"].config(text=accuracy_text)

            # AS and MS are traverse-wide results, so they are written
            # into the last station row rather than duplicated on every row.
            # The observation cells remain editable.
            last_station = station_rows[-1]
            set_entry(last_station["as"], f"{misclosure_seconds:+.2f} sec")
            set_entry(last_station["ms"], f"{linear_misclosure:.3f} m")

            # ----------------------------------------------
            # HISTORY
            # ----------------------------------------------

            from datetime import datetime
            now = datetime.now()

            detail_lines = [
                "GCAE TRAVERSE CALCULATION",
                "=" * 80,
                f"Date/Time: {now.strftime('%Y-%m-%d %H:%M:%S')}",
                f"Number of Stations: {n}",
                f"Starting Northing: {x0:.3f}",
                f"Starting Easting: {y0:.3f}",
                f"Starting Bearing: {start_bearing:.6f}°",
                "",
                "STATIONS / OBSERVATIONS",
                "-" * 80,
            ]

            for i, sr in enumerate(station_rows):
                detail_lines.append(
                    f"Station {i+1}: {sr['station'].get()} | "
                    f"Angle: {sr['angle_d'].get()}° "
                    f"{sr['angle_m'].get()}' "
                    f"{sr['angle_s'].get()}'' | "
                    f"Angle correction: {sr['angle_cor'].get()} sec"
                )

            detail_lines.extend(["", "TRAVERSE RESULTS", "-" * 80])

            for i, lr in enumerate(leg_rows):
                detail_lines.append(
                    f"Line {i+1}: Bearing {lr['bearing_d'].get()}° "
                    f"{lr['bearing_m'].get()}' {lr['bearing_s'].get()}'' | "
                    f"Distance {lr['distance'].get()} m | "
                    f"ΔN {lr['dn'].cget('text')} m | "
                    f"Corr N {lr['corr_n'].cget('text')} m | "
                    f"ΔE {lr['de'].cget('text')} m | "
                    f"Corr E {lr['corr_e'].cget('text')} m"
                )

            detail_lines.extend([
                "",
                f"Total Distance: {total_distance:.3f} m",
                f"N Misclosure: {sum_dn:.3f} m",
                f"E Misclosure: {sum_de:.3f} m",
                f"Angular Misclosure (AS): {misclosure_seconds:+.2f} sec",
                f"Angular Correction: {correction_seconds:+.2f} sec/stn",
                f"Linear Misclosure (MS): {linear_misclosure:.3f} m",
                f"Accuracy: {accuracy_text}",
            ])

            calculation_history.append({
                "time": now.strftime("%Y-%m-%d %H:%M:%S"),
                "stations": n,
                "distance": f"{total_distance:.3f} m",
                "as": f"{misclosure_seconds:+.2f} sec",
                "ms": f"{linear_misclosure:.3f} m",
                "nmis": f"{sum_dn:.3f} m",
                "emis": f"{sum_de:.3f} m",
                "linear": f"{linear_misclosure:.3f} m",
                "accuracy": accuracy_text,
                "details": "\n".join(detail_lines),
            })

            status.config(
                text=(
                    "Calculation updated successfully. "
                    "All input data remain editable."
                )
            )

        except ValueError as error:
            # NOTHING IS CLEARED.
            # The user can press OK, fill the missing field and
            # calculate again from the same table.
            messagebox.showerror(
                "Incomplete / Invalid Data",
                str(error)
            )

        except Exception as error:
            # NOTHING IS CLEARED here either.
            messagebox.showerror(
                "Calculation Error",
                f"Please check the entered data.\n\n{error}"
            )

    # --------------------------------------------------------
    # INITIAL INSTRUCTION
    # --------------------------------------------------------

    tk.Label(
        tw,
        text=(
            "Input data remain editable after calculation. "
            "Correct a value and press CALCULATE / UPDATE."
        ),
        font=("Arial", 9, "italic")
    ).pack(pady=3)


def setup_menu():

    menu_bar = tk.Menu(window)

    # FILE
    file_menu = tk.Menu(menu_bar, tearoff=0)
    file_menu.add_command(label="New Project")
    file_menu.add_command(label="Open Project")
    file_menu.add_command(label="Save Project")
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=window.destroy)
    menu_bar.add_cascade(label="File", menu=file_menu)

    # SURVEY
    survey_menu = tk.Menu(menu_bar, tearoff=0)
    survey_menu.add_command(label="Rise & Fall")
    survey_menu.add_command(label="Height of Instrument")
    survey_menu.add_command(label="Traverse", command=open_traverse)
    survey_menu.add_command(label="Bearing & Distance")
    survey_menu.add_command(label="Coordinates")
    survey_menu.add_command(label="Area")
    survey_menu.add_command(label="Road Width")
    survey_menu.add_command(label="Tacheometry")
    menu_bar.add_cascade(label="Survey", menu=survey_menu)

    # CALCULATIONS
    calc_menu = tk.Menu(menu_bar, tearoff=0)
    calc_menu.add_command(label="Transform")
    calc_menu.add_command(label="Join Computations")
    calc_menu.add_command(label="Triangle Solution")
    menu_bar.add_cascade(label="Calculations", menu=calc_menu)

    # DATA
    data_menu = tk.Menu(menu_bar, tearoff=0)
    data_menu.add_command(label="Data Sheet")
    data_menu.add_command(label="Import Excel")
    data_menu.add_command(label="Export Excel")
    data_menu.add_command(label="Export PDF")
    menu_bar.add_cascade(label="Data", menu=data_menu)

    # TOOLS
    tools_menu = tk.Menu(menu_bar, tearoff=0)
    tools_menu.add_command(label="Settings")
    menu_bar.add_cascade(label="Tools", menu=tools_menu)

    # HELP
    help_menu = tk.Menu(menu_bar, tearoff=0)
    help_menu.add_command(label="About GCAE")
    menu_bar.add_cascade(label="Help", menu=help_menu)

    window.config(menu=menu_bar)



# ============================================================
# START
# ============================================================

setup_menu()
window.mainloop()
