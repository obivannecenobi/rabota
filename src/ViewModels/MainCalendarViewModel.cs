using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.IO;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Windows.Input;
using System.Windows.Media;

namespace CalendarApp.ViewModels
{
    public class MainCalendarViewModel : INotifyPropertyChanged
    {
        public ObservableCollection<DayTask> Days { get; set; } = new ObservableCollection<DayTask>();
        public ObservableCollection<int> Years { get; } = new ObservableCollection<int>();
        public ObservableCollection<int> Months { get; } = new ObservableCollection<int>();
        public ObservableCollection<Priority> Priorities { get; } = new ObservableCollection<Priority> { Priority.Low, Priority.Medium, Priority.High };

        private int selectedYear;
        public int SelectedYear
        {
            get => selectedYear;
            set
            {
                if (selectedYear != value)
                {
                    selectedYear = value;
                    OnPropertyChanged(nameof(SelectedYear));
                    GenerateCalendar();
                    LoadData();
                }
            }
        }

        private int selectedMonth;
        public int SelectedMonth
        {
            get => selectedMonth;
            set
            {
                if (selectedMonth != value)
                {
                    selectedMonth = value;
                    OnPropertyChanged(nameof(SelectedMonth));
                    GenerateCalendar();
                    LoadData();
                }
            }
        }

        public ICommand SaveCommand { get; }
        public ICommand LoadCommand { get; }

        public MainCalendarViewModel()
        {
            for (int y = DateTime.Now.Year - 5; y <= DateTime.Now.Year + 5; y++)
                Years.Add(y);
            for (int m = 1; m <= 12; m++)
                Months.Add(m);

            SelectedYear = DateTime.Now.Year;
            SelectedMonth = DateTime.Now.Month;

            SaveCommand = new RelayCommand(_ => SaveData());
            LoadCommand = new RelayCommand(_ => { GenerateCalendar(); LoadData(); });

            GenerateCalendar();
            LoadData();
        }

        private string DataFilePath => Path.Combine(AppDomain.CurrentDomain.BaseDirectory, $"calendar_{SelectedYear}_{SelectedMonth}.json");

        private void GenerateCalendar()
        {
            Days.Clear();
            int daysInMonth = DateTime.DaysInMonth(SelectedYear, SelectedMonth);
            for (int day = 1; day <= daysInMonth; day++)
            {
                Days.Add(new DayTask { Date = new DateTime(SelectedYear, SelectedMonth, day) });
            }
        }

        private void SaveData()
        {
            var options = new JsonSerializerOptions { WriteIndented = true };
            File.WriteAllText(DataFilePath, JsonSerializer.Serialize(Days, options));
        }

        private void LoadData()
        {
            if (File.Exists(DataFilePath))
            {
                var json = File.ReadAllText(DataFilePath);
                var items = JsonSerializer.Deserialize<ObservableCollection<DayTask>>(json);
                if (items != null)
                {
                    Days.Clear();
                    foreach (var item in items) Days.Add(item);
                }
            }
        }

        public event PropertyChangedEventHandler PropertyChanged;
        private void OnPropertyChanged(string name) => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));

        public class DayTask : INotifyPropertyChanged
        {
            public DateTime Date { get; set; }

            private string plan;
            public string Plan
            {
                get => plan;
                set { plan = value; OnPropertyChanged(nameof(Plan)); }
            }

            private string done;
            public string Done
            {
                get => done;
                set { done = value; OnPropertyChanged(nameof(Done)); }
            }

            private Priority priority;
            public Priority Priority
            {
                get => priority;
                set { priority = value; OnPropertyChanged(nameof(Priority)); OnPropertyChanged(nameof(PriorityBrush)); }
            }

            [JsonIgnore]
            public Brush PriorityBrush
            {
                get
                {
                    return Priority switch
                    {
                        Priority.Low => Brushes.LightGreen,
                        Priority.Medium => Brushes.Khaki,
                        Priority.High => Brushes.Salmon,
                        _ => Brushes.White
                    };
                }
            }

            public event PropertyChangedEventHandler PropertyChanged;
            private void OnPropertyChanged(string name) => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
        }

        public enum Priority
        {
            Low,
            Medium,
            High
        }

        private class RelayCommand : ICommand
        {
            private readonly Action<object> execute;
            public RelayCommand(Action<object> execute) => this.execute = execute;
            public bool CanExecute(object parameter) => true;
            public void Execute(object parameter) => execute(parameter);
            public event EventHandler CanExecuteChanged { add { } remove { } }
        }
    }
}
