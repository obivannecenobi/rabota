using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Windows.Input;

namespace CalendarApp.ViewModels
{
    public class TopMonthViewModel : INotifyPropertyChanged
    {
        public ObservableCollection<MonthSummary> Summaries { get; } = new();
        public ObservableCollection<ReportSummary> QuarterlyReport { get; } = new();
        private ReportSummary yearlyReport = new ReportSummary();
        public ReportSummary YearlyReport
        {
            get => yearlyReport;
            private set { yearlyReport = value; OnPropertyChanged(nameof(YearlyReport)); }
        }

        public ICommand SaveCommand { get; }
        public ICommand LoadCommand { get; }

        public TopMonthViewModel()
        {
            for (int m = 1; m <= 12; m++)
            {
                var summary = new MonthSummary { Month = m };
                summary.PropertyChanged += (_, __) => UpdateReports();
                Summaries.Add(summary);
            }

            SaveCommand = new RelayCommand(_ => { SaveData(); UpdateReports(); });
            LoadCommand = new RelayCommand(_ => { LoadData(); UpdateReports(); });

            LoadData();
            UpdateReports();
        }

        private string DataFilePath => Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "topmonth_metrics.json");

        private void SaveData()
        {
            var options = new JsonSerializerOptions { WriteIndented = true };
            File.WriteAllText(DataFilePath, JsonSerializer.Serialize(Summaries, options));
        }

        private void LoadData()
        {
            if (File.Exists(DataFilePath))
            {
                var json = File.ReadAllText(DataFilePath);
                var items = JsonSerializer.Deserialize<ObservableCollection<MonthSummary>>(json);
                if (items != null && items.Count == 12)
                {
                    Summaries.Clear();
                    foreach (var item in items)
                    {
                        item.PropertyChanged += (_, __) => UpdateReports();
                        Summaries.Add(item);
                    }
                }
            }
        }

        private void UpdateReports()
        {
            QuarterlyReport.Clear();
            foreach (var grp in Summaries.GroupBy(s => (s.Month - 1) / 3 + 1))
            {
                QuarterlyReport.Add(new ReportSummary
                {
                    Period = $"Q{grp.Key}",
                    Profit = grp.Sum(x => x.Profit),
                    Views = grp.Sum(x => x.Views)
                });
            }

            YearlyReport = new ReportSummary
            {
                Period = "Year",
                Profit = Summaries.Sum(x => x.Profit),
                Views = Summaries.Sum(x => x.Views)
            };
        }

        public event PropertyChangedEventHandler PropertyChanged;
        private void OnPropertyChanged(string name) => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));

        public class MonthSummary : INotifyPropertyChanged
        {
            public int Month { get; set; }

            private decimal profit;
            public decimal Profit
            {
                get => profit;
                set { profit = value; OnPropertyChanged(nameof(Profit)); }
            }

            private int views;
            public int Views
            {
                get => views;
                set { views = value; OnPropertyChanged(nameof(Views)); }
            }

            public event PropertyChangedEventHandler PropertyChanged;
            private void OnPropertyChanged(string name) => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
        }

        public class ReportSummary
        {
            public string Period { get; set; }
            public decimal Profit { get; set; }
            public int Views { get; set; }
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
