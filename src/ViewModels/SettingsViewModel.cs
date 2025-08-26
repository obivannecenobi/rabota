using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Windows.Media;
using CalendarApp.Services;

namespace CalendarApp.ViewModels
{
    public class SettingsViewModel : INotifyPropertyChanged
    {
        private readonly MainCalendarViewModel calendar;

        public ObservableCollection<string> Themes { get; } = new() { "Light", "Dark" };
        private string selectedTheme;
        public string SelectedTheme
        {
            get => selectedTheme;
            set
            {
                if (selectedTheme != value)
                {
                    selectedTheme = value;
                    OnPropertyChanged(nameof(SelectedTheme));
                }
            }
        }

        public ObservableCollection<Brush> Palette { get; } = new() { Brushes.Blue, Brushes.Green, Brushes.Red, Brushes.Purple };
        private Brush selectedColor;
        public Brush SelectedColor
        {
            get => selectedColor;
            set
            {
                if (selectedColor != value)
                {
                    selectedColor = value;
                    OnPropertyChanged(nameof(SelectedColor));
                }
            }
        }

        public ObservableCollection<string> Fonts { get; } = new() { "Arial", "Segoe UI", "Times New Roman" };
        private string selectedFont;
        public string SelectedFont
        {
            get => selectedFont;
            set
            {
                if (selectedFont != value)
                {
                    selectedFont = value;
                    OnPropertyChanged(nameof(SelectedFont));
                }
            }
        }

        public ObservableCollection<Brush> NeonColors { get; } = new() { Brushes.Cyan, Brushes.Magenta, Brushes.Lime };
        private Brush selectedNeonColor;
        public Brush SelectedNeonColor
        {
            get => selectedNeonColor;
            set
            {
                if (selectedNeonColor != value)
                {
                    selectedNeonColor = value;
                    OnPropertyChanged(nameof(SelectedNeonColor));
                }
            }
        }

        private bool neonEnabled;
        public bool NeonEnabled
        {
            get => neonEnabled;
            set
            {
                if (neonEnabled != value)
                {
                    neonEnabled = value;
                    OnPropertyChanged(nameof(NeonEnabled));
                }
            }
        }

        private double neonIntensity = 0.5;
        public double NeonIntensity
        {
            get => neonIntensity;
            set
            {
                if (neonIntensity != value)
                {
                    neonIntensity = value;
                    OnPropertyChanged(nameof(NeonIntensity));
                }
            }
        }

        public ObservableCollection<PriorityFilter> PriorityFilters => calendar.Filters;
        public PriorityFilter SelectedPriorityFilter
        {
            get => calendar.SelectedFilter;
            set
            {
                if (calendar.SelectedFilter != value)
                {
                    calendar.SelectedFilter = value;
                    OnPropertyChanged(nameof(SelectedPriorityFilter));
                }
            }
        }

        private double panelScale = 1.0;
        public double PanelScale
        {
            get => panelScale;
            set
            {
                if (panelScale != value)
                {
                    panelScale = value;
                    OnPropertyChanged(nameof(PanelScale));
                }
            }
        }

        public SettingsViewModel(MainCalendarViewModel calendar)
        {
            this.calendar = calendar;
            SelectedTheme = Themes[0];
            selectedColor = Palette[0];
            selectedFont = Fonts[0];
            selectedNeonColor = NeonColors[0];
        }

        public event PropertyChangedEventHandler PropertyChanged;
        private void OnPropertyChanged(string name) => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
    }
}
