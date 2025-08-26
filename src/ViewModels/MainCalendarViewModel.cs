using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Linq;
using System.Text.Json.Serialization;
using System.Windows.Input;
using System.Windows.Media;
using CalendarApp.Services;
using CalendarApp.Data;

namespace CalendarApp.ViewModels
{
    public class MainCalendarViewModel : INotifyPropertyChanged
    {
        public ObservableCollection<DayTask> Days { get; set; } = new ObservableCollection<DayTask>();
        public ObservableCollection<int> Years { get; } = new ObservableCollection<int>();
        public ObservableCollection<int> Months { get; } = new ObservableCollection<int>();
        public ObservableCollection<PriorityLevel> Priorities { get; } = new ObservableCollection<PriorityLevel>(PriorityService.GetPriorities());
        public ObservableCollection<PriorityFilter> Filters { get; } = new ObservableCollection<PriorityFilter> { PriorityFilter.OneToFour, PriorityFilter.OneToTwo };

        private PriorityFilter selectedFilter = PriorityFilter.OneToFour;
        public PriorityFilter SelectedFilter
        {
            get => selectedFilter;
            set
            {
                if (selectedFilter != value)
                {
                    selectedFilter = value;
                    OnPropertyChanged(nameof(SelectedFilter));
                    ApplySortAndFilter();
                }
            }
        }

        private int selectedYear;
        public int SelectedYear
        {
            get => selectedYear;
            set
            {
                if (selectedYear != value)
                {
                    SaveData();
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
                    SaveData();
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
            ApplySortAndFilter();

            AppDomain.CurrentDomain.ProcessExit += (_, __) => SaveData();
        }

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
            if (SelectedYear == 0 || SelectedMonth == 0) return;
            DataStore.Save(Days, SelectedYear, SelectedMonth);
        }

        private void LoadData()
        {
            var items = DataStore.Load<ObservableCollection<DayTask>>(SelectedYear, SelectedMonth);
            if (items != null)
            {
                Days.Clear();
                foreach (var item in items) Days.Add(item);
            }

            ApplySortAndFilter();
        }

        public event PropertyChangedEventHandler PropertyChanged;
        private void OnPropertyChanged(string name) => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));

        public class DayTask : INotifyPropertyChanged
        {
            public DayTask()
            {
                Priority = PriorityLevel.One;
            }

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

            private PriorityLevel priority;
            public PriorityLevel Priority
            {
                get => priority;
                set { priority = value; OnPropertyChanged(nameof(Priority)); OnPropertyChanged(nameof(PriorityBrush)); }
            }

            [JsonIgnore]
            public Brush PriorityBrush => PriorityService.GetBrush(Priority);

            public event PropertyChangedEventHandler PropertyChanged;
            private void OnPropertyChanged(string name) => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
        }

        private void ApplySortAndFilter()
        {
            var sorted = PriorityService.Sort(Days);
            var filtered = PriorityService.Filter(sorted, SelectedFilter).ToList();
            Days.Clear();
            foreach (var item in filtered) Days.Add(item);
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
