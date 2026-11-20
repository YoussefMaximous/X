#property strict

int info_handle = -1;
int tick_handle = -1;

int OnInit()
  {
   if(!IsTesting()) return(INIT_FAILED);

   Print("LossLensProbe init start");
   info_handle = FileOpen("losslens_probe_info.txt", FILE_TXT|FILE_WRITE|FILE_ANSI);
   if(info_handle < 0)
     {
      Print("LossLensProbe info open failed: ", GetLastError());
      return(INIT_FAILED);
     }

   FileWriteString(info_handle, "Symbol=" + Symbol() + "\r\n");
   FileWriteString(info_handle, "Period=" + IntegerToString(Period()) + "\r\n");
   FileWriteString(info_handle, "Digits=" + IntegerToString(Digits) + "\r\n");
   FileWriteString(info_handle, "Point=" + DoubleToString(Point, 8) + "\r\n");
   FileWriteString(info_handle, "MODE_SPREAD=" + DoubleToString(MarketInfo(Symbol(), MODE_SPREAD), 8) + "\r\n");
   FileWriteString(info_handle, "MODE_STOPLEVEL=" + DoubleToString(MarketInfo(Symbol(), MODE_STOPLEVEL), 8) + "\r\n");
   FileWriteString(info_handle, "MODE_FREEZELEVEL=" + DoubleToString(MarketInfo(Symbol(), MODE_FREEZELEVEL), 8) + "\r\n");
   FileWriteString(info_handle, "MODE_TICKVALUE=" + DoubleToString(MarketInfo(Symbol(), MODE_TICKVALUE), 8) + "\r\n");
   FileWriteString(info_handle, "MODE_TICKSIZE=" + DoubleToString(MarketInfo(Symbol(), MODE_TICKSIZE), 8) + "\r\n");
   FileWriteString(info_handle, "MODE_LOTSIZE=" + DoubleToString(MarketInfo(Symbol(), MODE_LOTSIZE), 8) + "\r\n");
   FileWriteString(info_handle, "MODE_MINLOT=" + DoubleToString(MarketInfo(Symbol(), MODE_MINLOT), 8) + "\r\n");
   FileWriteString(info_handle, "MODE_LOTSTEP=" + DoubleToString(MarketInfo(Symbol(), MODE_LOTSTEP), 8) + "\r\n");
   FileWriteString(info_handle, "MODE_MAXLOT=" + DoubleToString(MarketInfo(Symbol(), MODE_MAXLOT), 8) + "\r\n");
   FileWriteString(info_handle, "MODE_SWAPLONG=" + DoubleToString(MarketInfo(Symbol(), MODE_SWAPLONG), 8) + "\r\n");
   FileWriteString(info_handle, "MODE_SWAPSHORT=" + DoubleToString(MarketInfo(Symbol(), MODE_SWAPSHORT), 8) + "\r\n");
   FileWriteString(info_handle, "MODE_PROFITCALCMODE=" + DoubleToString(MarketInfo(Symbol(), MODE_PROFITCALCMODE), 8) + "\r\n");
   FileWriteString(info_handle, "MODE_MARGINREQUIRED=" + DoubleToString(MarketInfo(Symbol(), MODE_MARGINREQUIRED), 8) + "\r\n");
   FileWriteString(info_handle, "AccountBalance=" + DoubleToString(AccountBalance(), 8) + "\r\n");
   FileWriteString(info_handle, "AccountCurrency=" + AccountCurrency() + "\r\n");
   FileWriteString(info_handle, "AccountLeverage=" + IntegerToString(AccountLeverage()) + "\r\n");
   FileWriteString(info_handle, "IsVisualMode=" + IntegerToString(IsVisualMode()) + "\r\n");
   FileWriteString(info_handle, "TerminalBuild=" + IntegerToString(TerminalInfoInteger(TERMINAL_BUILD)) + "\r\n");
   FileClose(info_handle);
   info_handle = -1;

   tick_handle = FileOpen("losslens_probe_ticks.bin", FILE_BIN|FILE_WRITE);
   if(tick_handle < 0)
     {
      Print("LossLensProbe tick open failed: ", GetLastError());
      return(INIT_FAILED);
     }
   Print("LossLensProbe init ok");
   return(INIT_SUCCEEDED);
  }

void OnTick()
  {
   if(tick_handle < 0) return;
   FileWriteLong(tick_handle, (long)TimeCurrent());
   FileWriteDouble(tick_handle, Bid);
   FileWriteDouble(tick_handle, Ask);
   FileWriteLong(tick_handle, (long)Volume[0]);
   FileWriteLong(tick_handle, (long)Time[0]);
  }

void OnDeinit(const int reason)
  {
   if(tick_handle >= 0)
     {
      FileClose(tick_handle);
      tick_handle = -1;
     }
   if(info_handle >= 0)
     {
      FileClose(info_handle);
      info_handle = -1;
     }
  }
