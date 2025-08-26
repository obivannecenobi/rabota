using System.Collections.ObjectModel;
using System.ComponentModel;

namespace CalendarApp.ViewModels
{
    public class PostScheduleViewModel : INotifyPropertyChanged
    {
        private readonly MainCalendarViewModel calendar;

        public ObservableCollection<MainCalendarViewModel.DayTask> Days => calendar.Days;
        public ObservableCollection<MainCalendarViewModel.Priority> Priorities => calendar.Priorities;

        public PostScheduleViewModel(MainCalendarViewModel calendar)
        {
            this.calendar = calendar;
        }

        public event PropertyChangedEventHandler PropertyChanged;
        private void OnPropertyChanged(string name) => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
    }
}
