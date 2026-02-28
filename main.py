import datetime
import sqlite3
import os
from statistics import mean
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json

print("Hello, World!")

class StudyCourse:
    """
    Repräsentiert einen Studiengang mit zugehörigen Modulen.
    
    Attribute:
        name: Name des Studiengangs
        course_id: Eindeutige Kennung des Studiengangs
        duration_semesters: Regelstudienzeit in Semestern
        modules: Liste der zugehörigen Module
    """
    def __init__(self, name, course_id, duration_semesters):
        """Initialisiert einen neuen Studiengang."""
        self.name = name
        self.course_id = course_id
        self.duration_semesters = duration_semesters
        self.modules = []
    
    def add_module(self, module):
        """Fügt ein Modul zum Studiengang hinzu."""
        self.modules.append(module)

class Student:
    """
    Repräsentiert einen Studenten.
    
    Attribute:
        name: Vollständiger Name des Studenten
        student_id: Matrikelnummer
        study_course: Zugeordneter Studiengang
    """
    def __init__(self, name, student_id, study_course):
        """Initialisiert einen neuen Studenten."""
        self.name = name
        self.student_id = student_id
        self.study_course = study_course

class Semester:
    """
    Repräsentiert ein Semester.
    
    Attribute:
        number: Semesternummer (z.B. 1, 2, 3)
        year: Jahr des Semesters
    """
    def __init__(self, number, year):
        """Initialisiert ein neues Semester."""
        self.number = number
        self.year = year

class Module:
    """
    Repräsentiert ein Studienmodul.
    
    Attribute:
        name: Name des Moduls
        module_id: Eindeutige Modulkennung
        credits: ECTS-Punkte des Moduls
    """
    def __init__(self, name, module_id, credits):
        """Initialisiert ein neues Modul."""
        self.name = name
        self.module_id = module_id
        self.credits = credits

class Exam:
    """
    Repräsentiert eine Prüfung eines Studenten in einem Modul.
    
    Attribute:
        module: Das zugehörige Modul
        student: Der zugehörige Student
        semester: Das Semester der Prüfung
        grade: Die erzielte Note (None wenn noch nicht bewertet)
    """
    def __init__(self, module, student, semester, grade=None):
        """Initialisiert eine neue Prüfung."""
        self.module = module
        self.student = student
        self.semester = semester
        self.grade = grade

class Database:
    """
    Verwaltet die SQLite-Datenbankverbindung und -operationen.
    
    Speichert Dashboard-Daten, Fristen und abgeschlossene Module persistent.
    """
    def __init__(self, db_name='student_dashboard.db'):
        """Initialisiert die Datenbank und erstellt ggf. die Tabellen."""
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Erstellt die Datenbanktabellen, falls sie noch nicht existieren."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS dashboard_data
                                (id INTEGER PRIMARY KEY, student_id TEXT, gpa REAL,
                                target_gpa REAL, target_end_date TEXT, avg_module_time INTEGER,
                                target_module_time INTEGER, last_updated TEXT)''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS deadlines
                                (id INTEGER PRIMARY KEY, student_id TEXT, deadline_type TEXT,
                                module_name TEXT, deadline_date TEXT)''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS completed_modules
                                (id INTEGER PRIMARY KEY, student_id TEXT, module_id TEXT,
                                completion_date TEXT, grade REAL)''')
    
    def save_dashboard_data(self, student_id, data):
        """Speichert oder aktualisiert die Dashboard-Daten eines Studenten."""
        with sqlite3.connect(self.db_name) as conn:
            conn.execute('''INSERT OR REPLACE INTO dashboard_data
                            (student_id, gpa, target_gpa, target_end_date, 
                            avg_module_time, target_module_time, last_updated)
                            VALUES (?, ?, ?, ?, ?, ?, ?)''',
                        (student_id, data['gpa'], data['target_gpa'],
                        data['target_end_date'], data['avg_module_time'],
                        data['target_module_time'], datetime.datetime.now().isoformat()))
    
    def update_target_gpa(self, student_id, target_gpa):
        """Aktualisiert die Ziel-Note eines Studenten."""
        with sqlite3.connect(self.db_name) as conn:
            conn.execute('''UPDATE dashboard_data SET target_gpa = ?, last_updated = ? 
                           WHERE student_id = ?''', 
                        (target_gpa, datetime.datetime.now().isoformat(), student_id))
    
    def update_target_end_date(self, student_id, target_end_date):
        """Aktualisiert das Ziel-Enddatum eines Studenten."""
        with sqlite3.connect(self.db_name) as conn:
            conn.execute('''UPDATE dashboard_data SET target_end_date = ?, last_updated = ? 
                           WHERE student_id = ?''', 
                        (target_end_date, datetime.datetime.now().isoformat(), student_id))
    
    def save_deadline(self, student_id, deadline_type, module_name, deadline_date):
        """Speichert eine neue Frist in der Datenbank."""
        with sqlite3.connect(self.db_name) as conn:
            conn.execute('''INSERT INTO deadlines (student_id, deadline_type, module_name, deadline_date)
                            VALUES (?, ?, ?, ?)''', (student_id, deadline_type, module_name, deadline_date))
    
    def delete_deadline(self, deadline_id):
        """Löscht eine Frist anhand ihrer ID."""
        with sqlite3.connect(self.db_name) as conn:
            conn.execute('DELETE FROM deadlines WHERE id = ?', (deadline_id,))
    
    def save_module_completion(self, student_id, module_id, grade, completion_date):
        """Speichert den Abschluss eines Moduls mit Note und Datum."""
        with sqlite3.connect(self.db_name) as conn:
            conn.execute('''INSERT OR REPLACE INTO completed_modules
                            (student_id, module_id, completion_date, grade)
                            VALUES (?, ?, ?, ?)''', (student_id, module_id, completion_date, grade))
    
    def get_completed_modules(self, student_id):
        """Gibt alle abgeschlossenen Module eines Studenten zurück."""
        with sqlite3.connect(self.db_name) as conn:
            return conn.execute('SELECT * FROM completed_modules WHERE student_id = ?', (student_id,)).fetchall()
    
    def get_deadlines(self, student_id):
        """Gibt alle Fristen eines Studenten sortiert nach Datum zurück."""
        with sqlite3.connect(self.db_name) as conn:
            return conn.execute('SELECT * FROM deadlines WHERE student_id = ? ORDER BY deadline_date',
                              (student_id,)).fetchall()


class GpaCalculator:
    """
    Berechnet den Notendurchschnitt und verwaltet die Ziel-Note.

    Attribute:
        target_gpa: Angestrebter Notendurchschnitt
    """
    def __init__(self, target_gpa: float, db: Database, student_id: str):
        """Initialisiert den GpaCalculator mit Ziel-Note und Datenbankzugang."""
        self.target_gpa = target_gpa
        self._db = db
        self._student_id = student_id

    def calculate(self, exams: list) -> float:
        """Berechnet den aktuellen Notendurchschnitt aller benoteten Prüfungen."""
        graded_exams = [exam for exam in exams if exam.grade is not None]
        return round(mean([exam.grade for exam in graded_exams]), 2) if graded_exams else 0.0

    def update_target(self, new_target_gpa: float):
        """Aktualisiert die Ziel-Note und speichert sie in der Datenbank."""
        self.target_gpa = new_target_gpa
        self._db.update_target_gpa(self._student_id, new_target_gpa)


class DeadlineManager:
    """
    Verwaltet Fristen: Hinzufügen, Löschen und Neuladen aus der Datenbank.

    Attribute:
        deadlines: Liste der aktuellen Fristen als Dictionaries
    """
    def __init__(self, student_id: str, db: Database):
        """Initialisiert den DeadlineManager mit Studenten-ID und Datenbankzugang."""
        self._student_id = student_id
        self._db = db
        self.deadlines = []

    def add(self, deadline_type: str, module_name: str, deadline_date: str):
        """Fügt eine neue Frist hinzu und speichert sie in der Datenbank."""
        self.deadlines.append({'type': deadline_type, 'module': module_name, 'date': deadline_date})
        self._db.save_deadline(self._student_id, deadline_type, module_name, deadline_date)

    def delete(self, index: int):
        """Löscht eine Frist anhand ihres Index."""
        if 0 <= index < len(self.deadlines):
            db_deadlines = self._db.get_deadlines(self._student_id)
            if index < len(db_deadlines):
                self._db.delete_deadline(db_deadlines[index][0])
            del self.deadlines[index]

    def reload(self):
        """Lädt alle Fristen aus der Datenbank neu."""
        self.deadlines = []
        for deadline in self._db.get_deadlines(self._student_id):
            self.deadlines.append({'type': deadline[2], 'module': deadline[3], 'date': deadline[4]})


class StudyProgressService:
    """
    Berechnet und verfolgt den Studienfortschritt:
    abgeschlossene Module, Bearbeitungszeit und voraussichtliches Studienende.

    Attribute:
        target_module_days: Ziel-Tage pro Modul
        target_end_date: Manuell gesetztes Ziel-Enddatum (optional)
    """
    def __init__(self, student: Student, target_module_days: int, db: Database):
        """Initialisiert den StudyProgressService."""
        self._student = student
        self._db = db
        self.target_module_days = target_module_days
        self.target_end_date = None

    def get_completed_modules(self, exams: list) -> list:
        """Gibt eine Liste aller bestandenen Module zurück (Note <= 4.0)."""
        return [exam.module for exam in exams if exam.grade is not None and exam.grade <= 4.0]

    def calculate_avg_module_time(self) -> int:
        """Berechnet die durchschnittliche Bearbeitungszeit pro Modul in Tagen."""
        return 45  # Platzhalter

    def calculate_target_end_date(self) -> str:
        """Berechnet das voraussichtliche Studienende basierend auf der Regelstudienzeit."""
        if self.target_end_date:
            return self.target_end_date
        remaining_semesters = self._student.study_course.duration_semesters
        end_date = datetime.datetime.now() + datetime.timedelta(days=remaining_semesters * 180)
        return end_date.strftime('%Y-%m-%d')

    def update_target_end_date(self, new_date: str):
        """Aktualisiert das Ziel-Enddatum und speichert es in der Datenbank."""
        self.target_end_date = new_date
        self._db.update_target_end_date(self._student.student_id, new_date)

    def save_module_completions(self, student_id: str, exams: list):
        """Speichert alle abgeschlossenen Module in der Datenbank."""
        for exam in exams:
            if exam.grade is not None and exam.grade <= 4.0:
                self._db.save_module_completion(student_id, exam.module.module_id,
                                                exam.grade, datetime.datetime.now().isoformat())


class Dashboard:
    """
    Zentrale Koordinationsklasse (Facade) für das Studenten-Dashboard.

    Delegiert GPA-Berechnungen an GpaCalculator, Fristenverwaltung an
    DeadlineManager und Studienfortschritt an StudyProgressService.
    """
    def __init__(self, student, target_gpa=3.0, target_module_days=60):
        """
        Initialisiert ein neues Dashboard für einen Studenten.

        Args:
            student: Der zugehörige Student
            target_gpa: Ziel-Notendurchschnitt (Standard: 3.0)
            target_module_days: Ziel-Tage pro Modul (Standard: 60)
        """
        self.student = student
        self.exams = []
        self._db = Database()
        self.gpa_calculator   = GpaCalculator(target_gpa, self._db, student.student_id)
        self.deadline_manager = DeadlineManager(student.student_id, self._db)
        self.study_progress   = StudyProgressService(student, target_module_days, self._db)

    @property
    def target_gpa(self):
        return self.gpa_calculator.target_gpa

    @property
    def deadlines(self):
        return self.deadline_manager.deadlines

    def add_exam(self, exam):
        """Fügt eine Prüfung zum Dashboard hinzu."""
        self.exams.append(exam)

    def add_deadline(self, deadline_type, module_name, deadline_date):
        """Fügt eine neue Frist hinzu."""
        self.deadline_manager.add(deadline_type, module_name, deadline_date)

    def update_target_gpa(self, new_target_gpa):
        """Aktualisiert die Ziel-Note."""
        self.gpa_calculator.update_target(new_target_gpa)

    def update_target_end_date(self, new_target_end_date):
        """Aktualisiert das Ziel-Enddatum."""
        self.study_progress.update_target_end_date(new_target_end_date)

    def delete_deadline(self, deadline_index):
        """Löscht eine Frist anhand ihres Index."""
        self.deadline_manager.delete(deadline_index)

    def reload_deadlines(self):
        """Lädt alle Fristen aus der Datenbank neu."""
        self.deadline_manager.reload()

    def calculate_gpa(self):
        """Berechnet den aktuellen Notendurchschnitt."""
        return self.gpa_calculator.calculate(self.exams)

    def calculate_avg_module_time(self):
        """Gibt die durchschnittliche Bearbeitungszeit pro Modul zurück."""
        return self.study_progress.calculate_avg_module_time()

    def calculate_target_end_date(self):
        """Berechnet das voraussichtliche Studienende."""
        return self.study_progress.calculate_target_end_date()

    def get_completed_modules(self):
        """Gibt eine Liste aller bestandenen Module zurück."""
        return self.study_progress.get_completed_modules(self.exams)

    def save_data(self):
        """Speichert alle Dashboard-Daten in der Datenbank."""
        data = {
            'gpa': self.calculate_gpa(),
            'target_gpa': self.target_gpa,
            'target_end_date': self.calculate_target_end_date(),
            'avg_module_time': self.calculate_avg_module_time(),
            'target_module_time': self.study_progress.target_module_days
        }
        self._db.save_dashboard_data(self.student.student_id, data)
        self.study_progress.save_module_completions(self.student.student_id, self.exams)

    def display(self):
        """Zeigt das Dashboard im Terminal an."""
        completed = self.get_completed_modules()
        total = self.student.study_course.modules

        print(f"\n{'='*50}")
        print(f"Dashboard for {self.student.name}")
        print(f"{'='*50}")
        print(f"Current GPA: {self.calculate_gpa()}")
        print(f"Target GPA: {self.target_gpa}")
        print(f"Target End Date: {self.calculate_target_end_date()}")
        print(f"Average Module Completion: {self.calculate_avg_module_time()} days")
        print(f"Target Module Completion: {self.study_progress.target_module_days} days")
        print(f"\nModule Progress: {len(completed)}/{len(total)} completed")
        print(f"Completed Modules:")
        for module in completed:
            print(f"  ✓ {module.name} ({module.credits} credits)")
        print(f"\nRemaining Modules:")
        for module in [m for m in total if m not in completed]:
            print(f"  ○ {module.name} ({module.credits} credits)")
        print(f"\nUpcoming Deadlines:")
        for deadline in sorted(self.deadlines, key=lambda x: x['date']):
            print(f"  {deadline['date']} - {deadline['type']}: {deadline['module']}")
        print(f"{'='*50}\n")


def load_dashboard_html():
    """
    Lädt die HTML-Vorlage aus der externen Datei dashboard.html.
    
    Returns:
        str: Der HTML-Inhalt als String
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(script_dir, 'dashboard.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        return f.read()
# Erstelle Testdaten
def create_test_data():
    """
    Erstellt Testdaten für das Dashboard.
    
    Erzeugt einen Beispiel-Studiengang mit Modulen, einen Studenten,
    Prüfungen und Fristen zur Demonstration der Funktionalität.
    
    Returns:
        Dashboard: Ein initialisiertes Dashboard mit Testdaten
    """
    course = StudyCourse("Cyber Security", "CS-2026", 6)
    
    modules = [
        Module("Objektorientierte mit Python", "CS101", 5),
        Module("Datenstrukturen", "CS102", 5),
        Module("Algorithmmen", "CS103", 5),
        Module("Databanken", "CS201", 5),
        Module("Web Development", "CS202", 5),
        Module("Software Engineering", "CS203", 5),
        Module("Maschinelles Lernen", "CS301", 5),
        Module("Cloud Computing", "CS302", 5),
    ]
    
    for module in modules:
        course.add_module(module)
    
    student = Student("Lukas Schwarzfeld", "IU123456789", course)
    dashboard = Dashboard(student, target_gpa=2.5, target_module_days=60)
    
    semester1 = Semester(1, 2023)
    semester2 = Semester(2, 2024)
    
    dashboard.add_exam(Exam(modules[0], student, semester1, 2.0))
    dashboard.add_exam(Exam(modules[1], student, semester1, 2.3))
    dashboard.add_exam(Exam(modules[2], student, semester1, 1.7))
    dashboard.add_exam(Exam(modules[3], student, semester2, 2.7))
    dashboard.add_exam(Exam(modules[4], student, semester2, 2.0))
    
    dashboard.add_exam(Exam(modules[5], student, semester2))
    dashboard.add_exam(Exam(modules[6], student, semester2))
    dashboard.add_exam(Exam(modules[7], student, semester2))
    
    # Lade existierende Deadlines aus der Datenbank
    dashboard.reload_deadlines()
    
    # Füge Testdaten nur hinzu, wenn noch keine Deadlines existieren
    if len(dashboard.deadlines) == 0:
        dashboard.add_deadline("Exam", "Software Engineering", "2024-06-15")
        dashboard.add_deadline("Assignment", "Machine Learning", "2024-06-20")
        dashboard.add_deadline("Project", "Cloud Computing", "2024-07-01")
        dashboard.add_deadline("Exam", "Machine Learning", "2024-07-10")
    
    dashboard.save_data()
    
    return dashboard


# Initialisiere Testdaten
dashboard = create_test_data()

class DashboardHandler(BaseHTTPRequestHandler):
    """
    HTTP-Request-Handler für das Web-Dashboard.
    
    Verarbeitet GET-Anfragen zur Anzeige des Dashboards und
    POST-Anfragen zur Aktualisierung von Daten (Fristen, Ziele).
    """
    def do_GET(self):
        """Verarbeitet GET-Anfragen und liefert die Dashboard-HTML-Seite."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            # Lade Deadlines aus der Datenbank neu
            dashboard.reload_deadlines()
            
            # Generiere Dashboard-HTML
            completed = dashboard.get_completed_modules()
            total = dashboard.student.study_course.modules
            completed_count = len(completed)
            total_count = len(total)
            progress = round((completed_count / total_count * 100) if total_count > 0 else 0, 1)
            
            # Erstelle HTML für abgeschlossene Module
            completed_html = ""
            for exam in dashboard.exams:
                if exam.grade is not None and exam.grade <= 4.0:
                    completed_html += f'''
                    <div class="module-card completed">
                        <strong>{exam.module.name}</strong><br>
                        Credits: {exam.module.credits}<br>
                        Grade: {exam.grade}
                    </div>
                    '''
            
            # Erstelle HTML für verbleibende Module
            remaining_html = ""
            for module in [m for m in total if m not in completed]:
                remaining_html += f'''
                <div class="module-card pending">
                    <strong>{module.name}</strong><br>
                    Credits: {module.credits}
                </div>
                '''
            
            # Erstelle HTML für Deadlines
            deadlines_html = ""
            for idx, deadline in enumerate(sorted(dashboard.deadlines, key=lambda x: x['date'])):
                deadlines_html += f'''
                <div class="deadline-item">
                    <div>
                        <span class="deadline-date">{deadline['date']}</span> - 
                        {deadline['type']}: {deadline['module']}
                    </div>
                    <button class="delete-btn" onclick="deleteDeadline({idx})">Delete</button>
                </div>
                '''
            
            # Formatiere das HTML
            html = load_dashboard_html()
            replacements = {
                '{student_name}': dashboard.student.name,
                '{gpa}': str(dashboard.calculate_gpa()),
                '{target_gpa}': str(dashboard.target_gpa),
                '{avg_time}': str(dashboard.calculate_avg_module_time()),
                '{end_date}': dashboard.calculate_target_end_date(),
                '{completed_count}': str(completed_count),
                '{total_count}': str(total_count),
                '{progress}': str(progress),
                '{completed_modules}': completed_html,
                '{remaining_modules}': remaining_html,
                '{deadlines}': deadlines_html,
            }
            for placeholder, value in replacements.items():
                html = html.replace(placeholder, value)
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """
        Verarbeitet POST-Anfragen für API-Operationen.
        
        Unterstützte Aktionen:
        - update_gpa: Aktualisiert die Ziel-Note
        - update_date: Aktualisiert das Ziel-Enddatum
        - add_deadline: Fügt eine neue Frist hinzu
        - delete_deadline: Löscht eine Frist
        """
        if self.path == '/api':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            params = parse_qs(post_data)
            
            action = params.get('action', [''])[0]
            response = {'success': False, 'message': 'Unknown action'}
            
            try:
                if action == 'update_gpa':
                    new_gpa = float(params.get('value', [''])[0])
                    dashboard.update_target_gpa(new_gpa)
                    response = {'success': True, 'message': 'Target GPA updated'}
                
                elif action == 'update_date':
                    new_date = params.get('value', [''])[0]
                    dashboard.update_target_end_date(new_date)
                    response = {'success': True, 'message': 'Target end date updated'}
                
                elif action == 'add_deadline':
                    deadline_type = params.get('type', [''])[0]
                    module_name = params.get('module', [''])[0]
                    deadline_date = params.get('date', [''])[0]
                    dashboard.add_deadline(deadline_type, module_name, deadline_date)
                    response = {'success': True, 'message': 'Deadline added'}
                
                elif action == 'delete_deadline':
                    index = int(params.get('index', [''])[0])
                    dashboard.delete_deadline(index)
                    dashboard.reload_deadlines()
                    response = {'success': True, 'message': 'Deadline deleted'}
            
            except Exception as e:
                response = {'success': False, 'message': str(e)}
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Gibt Log-Nachrichten mit Zeitstempel aus."""
        print(f"[{self.log_date_time_string()}] {format % args}")


class Server:
    """
    Kapselt den HTTP-Server: Konfiguration, Start und Ausgabe der Server-URL.

    Attribute:
        host: Hostname oder IP-Adresse
        port: Port-Nummer
    """
    def __init__(self, host='127.0.0.1', port=5000):
        """Initialisiert den Server mit Host und Port."""
        self.host = host
        self.port = port

    def start(self):
        """Startet den HTTP-Server und blockiert bis zum Abbruch."""
        httpd = HTTPServer((self.host, self.port), DashboardHandler)
        print("\n" + "*" * 60)
        print("Dashboard Server gestartet!")
        print(f"Dashboard URL: http://{self.host}:{self.port}")
        print("*" * 60 + "\n")
        httpd.serve_forever()


if __name__ == '__main__':
    Server().start()