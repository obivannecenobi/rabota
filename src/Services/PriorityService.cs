using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Media;
using CalendarApp.ViewModels;

namespace CalendarApp.Services
{
    public enum PriorityLevel
    {
        One = 1,
        Two,
        Three,
        Four
    }

    public enum PriorityFilter
    {
        OneToFour,
        OneToTwo
    }

    public static class PriorityService
    {
        private static readonly Dictionary<PriorityLevel, Brush> priorityColors = new()
        {
            { PriorityLevel.One, Brushes.LightGreen },
            { PriorityLevel.Two, Brushes.Khaki },
            { PriorityLevel.Three, Brushes.Salmon },
            { PriorityLevel.Four, Brushes.IndianRed }
        };

        private static readonly Dictionary<MainCalendarViewModel.DayTask, CancellationTokenSource> overrides = new();

        public static IEnumerable<PriorityLevel> GetPriorities()
        {
            return Enum.GetValues(typeof(PriorityLevel)).Cast<PriorityLevel>();
        }

        public static Brush GetBrush(PriorityLevel priority)
        {
            return priorityColors.TryGetValue(priority, out var brush) ? brush : Brushes.White;
        }

        public static IEnumerable<MainCalendarViewModel.DayTask> Sort(IEnumerable<MainCalendarViewModel.DayTask> tasks)
        {
            return tasks.OrderBy(t => t.Priority);
        }

        public static IEnumerable<MainCalendarViewModel.DayTask> Filter(IEnumerable<MainCalendarViewModel.DayTask> tasks, PriorityFilter filter)
        {
            return filter switch
            {
                PriorityFilter.OneToTwo => tasks.Where(t => (int)t.Priority <= 2),
                _ => tasks
            };
        }

        public static void OverridePriority(MainCalendarViewModel.DayTask task, PriorityLevel newPriority, TimeSpan duration)
        {
            var originalPriority = task.Priority;
            task.Priority = newPriority;
            var cts = new CancellationTokenSource();
            overrides[task] = cts;
            Task.Delay(duration, cts.Token).ContinueWith(t =>
            {
                if (!t.IsCanceled)
                {
                    task.Priority = originalPriority;
                }
                overrides.Remove(task);
            });
        }

        public static void CancelOverride(MainCalendarViewModel.DayTask task)
        {
            if (overrides.TryGetValue(task, out var cts))
            {
                cts.Cancel();
                overrides.Remove(task);
            }
        }
    }
}
