
import pandas as pd
import networkx as nx
from itertools import combinations


# BUOC 1: DOC VA KIEM TRA DU LIEU
def read_student_data(file_path="students.csv"):
    df = pd.read_csv(file_path)

    required_columns = {"StudentID", "Subject"}
    if not required_columns.issubset(df.columns):
        raise ValueError(
            "CSV phai co hai cot StudentID va Subject"
        )

    df = df[["StudentID", "Subject"]].copy()

    # Loai bo khoang trang va dong trung lap
    for col in ["StudentID", "Subject"]:
        df[col] = df[col].astype("string").str.strip()

    if df.isna().any().any() or (df == "").any().any():
        raise ValueError("Du lieu co o trong hoac bi thieu")

    df = df.drop_duplicates()

    if df.empty:
        raise ValueError("Khong co du lieu dang ky mon hoc")

    return df


# BUOC 2: XAY DUNG DO THI XUNG DOT
def build_conflict_graph(df):
    graph = nx.Graph()

    # Moi mon hoc la mot dinh
    subjects = sorted(df["Subject"].unique())
    graph.add_nodes_from(subjects)

    # Tim cac mon ma cung mot sinh vien dang ky
    for student_id, group in df.groupby("StudentID"):
        student_subjects = sorted(group["Subject"].unique())

        # Moi cap mon chung sinh vien tao thanh mot canh
        for subject_a, subject_b in combinations(
            student_subjects, 2
        ):
            if graph.has_edge(subject_a, subject_b):
                graph[subject_a][subject_b]["students"].append(
                    student_id
                )
            else:
                graph.add_edge(
                    subject_a,
                    subject_b,
                    students=[student_id]
                )

    return graph


# BUOC 3: TO MAU BANG GREEDY COLORING
def schedule_exams(graph):
    colors = nx.greedy_color(
        graph,
        strategy="largest_first"
    )

    # Mau 0 thanh Ca thi 1, mau 1 thanh Ca thi 2,...
    schedule = {
        subject: color + 1
        for subject, color in colors.items()
    }

    return schedule


# BUOC 4: KIEM TRA XUNG DOT
def validate_schedule(graph, schedule):
    conflicts = []

    for subject_a, subject_b in graph.edges():
        if schedule[subject_a] == schedule[subject_b]:
            conflicts.append((subject_a, subject_b))

    if conflicts:
        print("LICH THI CO XUNG DOT:")
        for subject_a, subject_b in conflicts:
            print(f"{subject_a} - {subject_b}")
        return False

    print("Lich thi hop le, khong co xung dot.")
    return True


# IN CAC CANH XUNG DOT
def print_conflict_graph(graph):
    print("\nDANH SACH MON HOC:")
    print(list(graph.nodes()))

    print("\nCAC CAP MON XUNG DOT:")
    for subject_a, subject_b, data in graph.edges(data=True):
        students = ", ".join(data["students"])
        print(
            f"{subject_a} <-> {subject_b}"
            f" | Sinh vien chung: {students}"
        )


# IN LICH THI THEO CA
def print_timetable(schedule):
    print("\nLICH THI:")

    for slot in sorted(set(schedule.values())):
        subjects = [
            subject
            for subject, color in schedule.items()
            if color == slot
        ]

        print(f"Ca thi {slot}: {', '.join(subjects)}")

    print(f"\nTong so ca thi: {len(set(schedule.values()))}")


# CHUONG TRINH CHINH
def main():
    df = read_student_data("students.csv")

    graph = build_conflict_graph(df)

    print_conflict_graph(graph)

    schedule = schedule_exams(graph)

    print_timetable(schedule)

    validate_schedule(graph, schedule)

    # Luu ket qua de nhom su dung
    result = pd.DataFrame(
        list(schedule.items()),
        columns=["Subject", "ExamSlot"]
    )
    result = result.sort_values(
        ["ExamSlot", "Subject"]
    )
    result.to_csv(
        "exam_schedule.csv",
        index=False,
        encoding="utf-8-sig"
    )

    print("\nDa luu ket qua vao exam_schedule.csv")


if __name__ == "__main__":
    main()
