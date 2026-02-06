namespace HardwoodHoops.Core;

public class GameClock
{
    private readonly int _secondsPerQuarter;
    private readonly int _totalQuarters;
    private int _currentQuarter = 1;
    private int _secondsRemaining;

    public GameClock(int secondsPerQuarter, int totalQuarters)
    {
        _secondsPerQuarter = secondsPerQuarter;
        _totalQuarters = totalQuarters;
        _secondsRemaining = secondsPerQuarter;
    }

    public bool IsFinalBuzzer => _currentQuarter > _totalQuarters;

    public void AdvanceSeconds(int seconds)
    {
        if (IsFinalBuzzer)
        {
            return;
        }

        _secondsRemaining -= seconds;
        while (_secondsRemaining <= 0 && _currentQuarter <= _totalQuarters)
        {
            _currentQuarter++;
            _secondsRemaining = _secondsPerQuarter + _secondsRemaining;
        }
    }

    public string FormatPeriodClock()
    {
        if (IsFinalBuzzer)
        {
            return "Final";
        }

        var minutes = _secondsRemaining / 60;
        var seconds = _secondsRemaining % 60;
        return $"Q{_currentQuarter} {minutes:00}:{seconds:00}";
    }

    public string FormatGameTime()
    {
        return $"[color=gray]{FormatPeriodClock()}[/color]";
    }
}
