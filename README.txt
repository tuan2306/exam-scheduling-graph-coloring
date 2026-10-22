EXAM SCHEDULING - INTEGRATED VERSION

Files:
- main.py: Tkinter UI, algorithm comparison, timetable, room assignment, Excel export.
- tuan_module.py: shared CSV validation and conflict graph construction from Tuan's code.
- students.csv: the supplied full registration dataset.

Run on Windows:
1. Install Python, then open Command Prompt/PowerShell in this folder.
2. Install dependencies:
   py -m pip install pandas networkx matplotlib openpyxl
3. Run:
   py main.py
4. Click Load Student CSV and select students.csv.
5. Choose an algorithm and click Generate Schedule.
6. Click Export Excel to save the workbook.

Room constraints: 10 rooms, 30 seats per room. A subject may use multiple rooms in the same slot.
