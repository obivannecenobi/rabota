using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Windows;

namespace CalendarApp.ViewModels
{
    public class StatisticsViewModel : INotifyPropertyChanged
    {
        public ObservableCollection<YearlyMetric> Metrics { get; } = new();
        public ObservableCollection<SoftwareCost> SoftwareCosts { get; } = new();
        public ObservableCollection<ChartSeries> Charts { get; } = new();
        public ObservableCollection<string> AvailableColors { get; } = new()
        {
            "Red", "Green", "Blue", "Orange", "Purple", "Black"
        };

        public StatisticsViewModel()
        {
            var currentYear = DateTime.Now.Year;
            for (int y = currentYear - 4; y <= currentYear; y++)
            {
                Metrics.Add(new YearlyMetric { Year = y });
            }

            SoftwareCosts.Add(new SoftwareCost { Name = "Licenses" });
            SoftwareCosts.Add(new SoftwareCost { Name = "Subscriptions" });

            Charts.Add(new ChartSeries { Name = "Profit", LineColor = "Green" });
            Charts.Add(new ChartSeries { Name = "Views", LineColor = "Blue" });
            Charts.Add(new ChartSeries { Name = "Software Cost", LineColor = "Orange" });
        }

        public event PropertyChangedEventHandler PropertyChanged;
        private void OnPropertyChanged(string name) => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));

        public class YearlyMetric : INotifyPropertyChanged
        {
            public int Year { get; set; }

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

            private decimal softwareCost;
            public decimal SoftwareCost
            {
                get => softwareCost;
                set { softwareCost = value; OnPropertyChanged(nameof(SoftwareCost)); }
            }

            public event PropertyChangedEventHandler PropertyChanged;
            private void OnPropertyChanged(string name) => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
        }

        public class SoftwareCost : INotifyPropertyChanged
        {
            public string Name { get; set; }

            private decimal cost;
            public decimal Cost
            {
                get => cost;
                set { cost = value; OnPropertyChanged(nameof(Cost)); }
            }

            public event PropertyChangedEventHandler PropertyChanged;
            private void OnPropertyChanged(string name) => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
        }

        public class ChartSeries : INotifyPropertyChanged
        {
            public string Name { get; set; }
            public ObservableCollection<Point> Points { get; } = new();

            private string lineColor = "Blue";
            public string LineColor
            {
                get => lineColor;
                set { lineColor = value; OnPropertyChanged(nameof(LineColor)); }
            }

            private bool isVisible = true;
            public bool IsVisible
            {
                get => isVisible;
                set { isVisible = value; OnPropertyChanged(nameof(IsVisible)); }
            }

            public event PropertyChangedEventHandler PropertyChanged;
            private void OnPropertyChanged(string name) => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
        }
    }
}
