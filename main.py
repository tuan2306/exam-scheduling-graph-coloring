import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Shared data/graph module developed by Tuan
from tuan_module import read_student_data, build_conflict_graph, validate_schedule


class ExamSchedulingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Automatic Exam Scheduling System")
        self.root.geometry("1300x900")
        self.root.minsize(1050, 700)

        # Graph and registration data
        self.graph = nx.Graph()
        self.student_data = None
        self.schedule = {}
        self.subject_counts = {}
        self.room_assignments = {}
        self.comparison_results = []

        # Text describing the loaded data (shown in the status bar)
        self.data_info = "Demo mode: sample conflict graph"

        # Room configuration
        self.ROOM_COUNT = 10
        self.ROOM_CAPACITY = 30

        self.algorithm = tk.StringVar(value="Welsh-Powell")

        self.create_ui()
        self.create_demo_graph()
        self.compare_algorithms()
        self.generate_schedule()

    # ==================================================
    # USER INTERFACE
    # ==================================================
    def create_ui(self):
        # Larger rows/fonts so tables stay readable in report screenshots
        style = ttk.Style()
        style.configure("Treeview", rowheight=24, font=("Arial", 10))
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

        tk.Label(
            self.root,
            text="AUTOMATIC EXAM SCHEDULING SYSTEM",
            font=("Arial", 18, "bold")
        ).pack(pady=10)

        controls = tk.Frame(self.root)
        controls.pack(pady=5)

        tk.Button(
            controls,
            text="Load Student CSV",
            command=self.load_csv,
            width=16
        ).pack(side=tk.LEFT, padx=4)

        tk.Button(
            controls,
            text="Compare Algorithms",
            command=self.compare_algorithms,
            width=18
        ).pack(side=tk.LEFT, padx=4)

        ttk.Label(
            controls,
            text="Algorithm:"
        ).pack(side=tk.LEFT, padx=(10, 3))

        ttk.Combobox(
            controls,
            textvariable=self.algorithm,
            values=["Greedy", "Welsh-Powell", "DSATUR"],
            state="readonly",
            width=16
        ).pack(side=tk.LEFT, padx=4)

        tk.Button(
            controls,
            text="Generate Schedule",
            command=self.generate_schedule,
            width=18
        ).pack(side=tk.LEFT, padx=4)

        tk.Button(
            controls,
            text="Export Excel",
            command=self.export_excel,
            width=14
        ).pack(side=tk.LEFT, padx=4)

        self.status = tk.Label(
            self.root,
            text=self.data_info,
            font=("Arial", 10)
        )
        self.status.pack(pady=5)

        # --------------------------------------------------
        # Resizable layout:
        #   main_pane (vertical)   = [ top_pane | comparison table ]
        #   top_pane (horizontal)  = [ graph | timetable ]
        # Drag the grey bars between the panels to resize them.
        # --------------------------------------------------
        main_pane = tk.PanedWindow(
            self.root,
            orient=tk.VERTICAL,
            sashwidth=8,
            sashrelief=tk.RAISED,
            sashpad=1
        )
        main_pane.pack(
            fill=tk.BOTH,
            expand=True,
            padx=10,
            pady=5
        )

        top_pane = tk.PanedWindow(
            main_pane,
            orient=tk.HORIZONTAL,
            sashwidth=8,
            sashrelief=tk.RAISED,
            sashpad=1
        )

        # Conflict graph
        graph_frame = tk.LabelFrame(
            top_pane,
            text="Subject Conflict Graph"
        )

        self.fig = Figure(figsize=(6, 5))
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(
            self.fig,
            master=graph_frame
        )
        self.canvas.get_tk_widget().pack(
            fill=tk.BOTH,
            expand=True
        )
        self.canvas.mpl_connect("resize_event", self.on_graph_resize)

        # Timetable
        table_frame = tk.LabelFrame(
            top_pane,
            text="Generated Exam Timetable"
        )

        columns = (
            "subject",
            "slot",
            "degree",
            "students",
            "room"
        )

        self.table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        headings = {
            "subject": "Subject",
            "slot": "Exam Slot",
            "degree": "Conflict Count",
            "students": "Students",
            "room": "Exam Room"
        }

        widths = {
            "subject": 200,
            "slot": 90,
            "degree": 105,
            "students": 75,
            "room": 180
        }

        for column in columns:
            self.table.heading(column, text=headings[column])
            self.table.column(
                column,
                width=widths[column],
                minwidth=60,
                anchor=tk.CENTER,
                stretch=True
            )

        self.table.column("subject", anchor=tk.W)

        table_scroll = ttk.Scrollbar(
            table_frame,
            orient=tk.VERTICAL,
            command=self.table.yview
        )
        self.table.configure(
            yscrollcommand=table_scroll.set
        )

        self.table.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True
        )
        table_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        top_pane.add(graph_frame, minsize=320, stretch="always")
        top_pane.add(table_frame, minsize=360, stretch="always")

        # Algorithm comparison
        compare_frame = tk.LabelFrame(
            main_pane,
            text="Algorithm Comparison"
        )

        compare_columns = (
            "algorithm",
            "slots",
            "runtime",
            "valid"
        )

        self.compare_table = ttk.Treeview(
            compare_frame,
            columns=compare_columns,
            show="headings",
            height=3
        )

        comparison_headings = {
            "algorithm": "Algorithm",
            "slots": "Number of Slots",
            "runtime": "Runtime (ms)",
            "valid": "Conflict-Free"
        }

        comparison_widths = {
            "algorithm": 220,
            "slots": 180,
            "runtime": 180,
            "valid": 180
        }

        for column in compare_columns:
            self.compare_table.heading(
                column,
                text=comparison_headings[column]
            )
            self.compare_table.column(
                column,
                width=comparison_widths[column],
                minwidth=80,
                anchor=tk.CENTER,
                stretch=True
            )

        self.compare_table.pack(
            fill=tk.BOTH,
            expand=True
        )

        main_pane.add(top_pane, minsize=250, stretch="always")
        main_pane.add(compare_frame, minsize=110, height=160, stretch="never")

    def on_graph_resize(self, event):
        """Keep the graph inside its panel when the panel is resized."""
        try:
            self.fig.tight_layout()
        except Exception:
            pass

    # ==================================================
    # DEMO GRAPH
    # ==================================================
    def create_demo_graph(self):
        self.graph.clear()

        subjects = [
            f"Subject {i:02d}"
            for i in range(1, 21)
        ]
        self.graph.add_nodes_from(subjects)

        edges = [
            (1, 2), (1, 3), (1, 5), (2, 3), (2, 4),
            (2, 7), (3, 4), (3, 6), (4, 5), (4, 8),
            (5, 6), (5, 9), (6, 7), (6, 10), (7, 8),
            (7, 11), (8, 9), (8, 12), (9, 10), (9, 13),
            (10, 11), (10, 14), (11, 12), (11, 15),
            (12, 13), (12, 16), (13, 14), (13, 17),
            (14, 15), (14, 18), (15, 16), (15, 19),
            (16, 17), (16, 20), (17, 18), (18, 19), (19, 20)
        ]

        for a, b in edges:
            self.graph.add_edge(
                f"Subject {a:02d}",
                f"Subject {b:02d}"
            )

    # ==================================================
    # LOAD CSV AND BUILD CONFLICT GRAPH
    # ==================================================
    def load_csv(self):
        filename = filedialog.askopenfilename(
            title="Select student registration CSV",
            filetypes=[("CSV files", "*.csv")]
        )

        if not filename:
            return

        try:
            # Use Tuan's shared module for CSV validation and conflict-graph construction.
            df = read_student_data(filename)
            graph = build_conflict_graph(df)

            self.student_data = df
            self.graph = graph

            # Set the data summary first so generate_schedule()
            # shows it together with the algorithm result.
            self.data_info = (
                f"Loaded {len(df)} registration records, "
                f"{self.graph.number_of_nodes()} subjects, "
                f"{self.graph.number_of_edges()} conflict edges"
            )

            self.compare_algorithms()
            self.generate_schedule()

            messagebox.showinfo(
                "Success",
                "CSV loaded and conflict graph created."
            )

        except pd.errors.EmptyDataError:
            messagebox.showerror(
                "CSV Error",
                "The selected CSV file is empty."
            )
        except Exception as error:
            messagebox.showerror(
                "CSV Error",
                str(error)
            )

    # ==================================================
    # GREEDY COLORING
    # ==================================================
    def greedy_coloring(self, ordered_nodes):
        colors = {}

        for node in ordered_nodes:
            unavailable = {
                colors[neighbor]
                for neighbor in self.graph.neighbors(node)
                if neighbor in colors
            }

            color = 0
            while color in unavailable:
                color += 1

            colors[node] = color

        return colors

    # ==================================================
    # WELSH-POWELL COLORING
    # ==================================================
    def welsh_powell_coloring(self):
        ordered = sorted(
            self.graph.nodes(),
            key=lambda node: (
                -self.graph.degree(node),
                str(node)
            )
        )

        return self.greedy_coloring(ordered)

    # ==================================================
    # RUN ONE COLORING ALGORITHM
    # ==================================================
    def run_algorithm(self, name):
        start = time.perf_counter()

        if name == "Greedy":
            coloring = self.greedy_coloring(
                list(self.graph.nodes())
            )

        elif name == "Welsh-Powell":
            coloring = self.welsh_powell_coloring()

        elif name == "DSATUR":
            coloring = nx.coloring.greedy_color(
                self.graph,
                strategy="saturation_largest_first"
            )

        else:
            raise ValueError(
                f"Unknown algorithm: {name}"
            )

        elapsed_ms = (
            time.perf_counter() - start
        ) * 1000

        # Check that every conflict edge connects different exam slots.
        valid = all(
            coloring[u] != coloring[v]
            for u, v in self.graph.edges()
        )

        slots = (
            max(coloring.values()) + 1
            if coloring else 0
        )

        return coloring, slots, elapsed_ms, valid

    # ==================================================
    # COMPARE ALGORITHMS
    # ==================================================
    def compare_algorithms(self):
        if not hasattr(self, "compare_table"):
            return

        for item in self.compare_table.get_children():
            self.compare_table.delete(item)

        self.comparison_results = []

        for name in [
            "Greedy",
            "Welsh-Powell",
            "DSATUR"
        ]:
            coloring, slots, elapsed, valid = (
                self.run_algorithm(name)
            )

            result = {
                "Algorithm": name,
                "NumberOfSlots": slots,
                "Runtime_ms": round(elapsed, 4),
                "ConflictFree": (
                    "Yes" if valid else "No"
                )
            }

            self.comparison_results.append(result)

            self.compare_table.insert(
                "",
                tk.END,
                values=(
                    name,
                    slots,
                    f"{elapsed:.4f}",
                    "Yes" if valid else "No"
                )
            )

    # ==================================================
    # COUNT STUDENTS AND ASSIGN ROOMS
    # ==================================================
    def assign_rooms(self, coloring):
        """
        Assign one or more rooms to each subject.
        A subject with more students than one room can hold is split
        across multiple rooms in the same exam slot.
        Rooms are reused in different slots.
        """
        self.room_assignments = {}
        self.subject_counts = {}

        if self.student_data is None:
            # Demo graph has no real registration data.
            self.subject_counts = {subject: 0 for subject in coloring}
        else:
            counts = (
                self.student_data.groupby("Subject")["StudentID"]
                .nunique()
                .to_dict()
            )
            self.subject_counts = {
                subject: int(counts.get(subject, 0))
                for subject in coloring
            }

        used_rooms_by_slot = {}
        ordered_subjects = sorted(
            coloring.items(),
            key=lambda item: (item[1], str(item[0]))
        )

        for subject, color in ordered_subjects:
            student_count = self.subject_counts[subject]
            slot = color + 1
            if slot not in used_rooms_by_slot:
                used_rooms_by_slot[slot] = set()

            # Even a subject with zero demo students gets one room.
            rooms_needed = max(
                1, (student_count + self.ROOM_CAPACITY - 1)
                // self.ROOM_CAPACITY
            )

            available_rooms = [
                room for room in range(1, self.ROOM_COUNT + 1)
                if room not in used_rooms_by_slot[slot]
            ]

            if len(available_rooms) < rooms_needed:
                rooms_available = len(available_rooms)
                raise ValueError(
                    f"Slot {slot} needs {rooms_needed} rooms for "
                    f"{subject} ({student_count} students), but only "
                    f"{rooms_available} room(s) remain. Increase "
                    f"ROOM_COUNT or choose an algorithm with fewer "
                    f"subjects/rooms in this slot."
                )

            assignments = []
            remaining_students = student_count

            for room in available_rooms[:rooms_needed]:
                assigned_students = min(
                    self.ROOM_CAPACITY, remaining_students
                )
                remaining_students -= assigned_students
                used_rooms_by_slot[slot].add(room)
                assignments.append({
                    "room": f"Room {room:02d}",
                    "students": assigned_students,
                    "capacity": self.ROOM_CAPACITY,
                    "seats_remaining": self.ROOM_CAPACITY - assigned_students,
                })

            self.room_assignments[subject] = assignments

    # ==================================================
    # GENERATE EXAM TIMETABLE
    # ==================================================
    def generate_schedule(self):
        if self.graph.number_of_nodes() == 0:
            return

        name = self.algorithm.get()

        try:
            coloring, slots, elapsed, valid = (
                self.run_algorithm(name)
            )

            if not valid:
                messagebox.showerror(
                    "Invalid Schedule",
                    "Conflicting subjects share the same slot."
                )
                return

            # Assign rooms before updating the timetable.
            self.assign_rooms(coloring)

        except Exception as error:
            messagebox.showerror(
                "Scheduling Error",
                str(error)
            )
            return

        self.schedule = coloring

        for item in self.table.get_children():
            self.table.delete(item)

        ordered = sorted(
            coloring.items(),
            key=lambda item: (item[1], str(item[0]))
        )

        for subject, color in ordered:
            self.table.insert(
                "",
                tk.END,
                values=(
                    subject,
                    f"Slot {color + 1}",
                    self.graph.degree(subject),
                    self.subject_counts.get(subject, 0),
                    ", ".join(room["room"] for room in self.room_assignments.get(subject, []))
                )
            )

        self.draw_graph()

        self.status.config(
            text=(
                f"{self.data_info}  |  "
                f"{name}: {len(coloring)} subjects, "
                f"{slots} slots, conflict-free: Yes, "
                f"runtime: {elapsed:.4f} ms, "
                f"rooms available per slot: {self.ROOM_COUNT}"
            )
        )

    # ==================================================
    # DRAW CONFLICT GRAPH
    # ==================================================
    def draw_graph(self):
        self.ax.clear()

        if self.graph.number_of_nodes() == 0:
            self.canvas.draw()
            return

        positions = nx.spring_layout(
            self.graph,
            seed=42
        )

        if self.schedule:
            node_colors = [
                self.schedule.get(node, 0)
                for node in self.graph.nodes()
            ]
        else:
            node_colors = "skyblue"

        nx.draw_networkx(
            self.graph,
            positions,
            ax=self.ax,
            node_color=node_colors,
            cmap=plt.cm.Set3,
            with_labels=True,
            font_size=7,
            node_size=650,
            edge_color="gray"
        )

        self.ax.set_title(
            "Each edge represents a subject conflict"
        )
        self.ax.axis("off")
        self.fig.tight_layout()
        self.canvas.draw()

    # ==================================================
    # EXPORT EXCEL
    # ==================================================
    def export_excel(self):
        if not self.schedule:
            messagebox.showwarning(
                "No Schedule",
                "Generate a schedule first."
            )
            return

        filename = filedialog.asksaveasfilename(
            title="Export exam schedule",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")]
        )

        if not filename:
            return

        try:
            timetable_rows = []
            room_rows = []

            for subject, color in sorted(
                self.schedule.items(),
                key=lambda item: (
                    item[1], str(item[0])
                )
            ):
                student_count = self.subject_counts.get(
                    subject, 0
                )
                room_list = self.room_assignments.get(subject, [])
                room_names = ", ".join(
                    room_info["room"] for room_info in room_list
                )

                timetable_rows.append({
                    "Subject": subject,
                    "ExamSlot": color + 1,
                    "ConflictCount": self.graph.degree(subject),
                    "StudentCount": student_count,
                    "Rooms": room_names,
                    "RoomCount": len(room_list),
                    "Algorithm": self.algorithm.get()
                })

                # One row per physical room, including the number of
                # students assigned to that room.
                for room_info in room_list:
                    room_rows.append({
                        "Subject": subject,
                        "ExamSlot": color + 1,
                        "StudentCountInRoom": room_info["students"],
                        "Room": room_info["room"],
                        "RoomCapacity": room_info["capacity"],
                        "SeatsRemaining": room_info["seats_remaining"]
                    })

            edge_rows = [
                {
                    "Subject A": u,
                    "Subject B": v
                }
                for u, v in self.graph.edges()
            ]

            with pd.ExcelWriter(
                filename,
                engine="openpyxl"
            ) as writer:

                pd.DataFrame(timetable_rows).to_excel(
                    writer,
                    sheet_name="Timetable",
                    index=False
                )

                pd.DataFrame(room_rows).to_excel(
                    writer,
                    sheet_name="Room Assignments",
                    index=False
                )

                pd.DataFrame(
                    self.comparison_results
                ).to_excel(
                    writer,
                    sheet_name="Algorithm Comparison",
                    index=False
                )

                pd.DataFrame(
                    edge_rows,
                    columns=["Subject A", "Subject B"]
                ).to_excel(
                    writer,
                    sheet_name="Conflict Edges",
                    index=False
                )

                if self.student_data is not None:
                    self.student_data.to_excel(
                        writer,
                        sheet_name="Registrations",
                        index=False
                    )

            messagebox.showinfo(
                "Export Successful",
                f"Excel file saved successfully:\n{filename}"
            )

        except Exception as error:
            messagebox.showerror(
                "Export Error",
                str(error)
            )


if __name__ == "__main__":
    root = tk.Tk()
    app = ExamSchedulingApp(root)
    root.mainloop()