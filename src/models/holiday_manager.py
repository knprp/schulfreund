import requests
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import logging
from requests.exceptions import RequestException, HTTPError, Timeout, ConnectionError

class HolidayAPIError(Exception):
    """Basisklasse für API-bezogene Fehler"""
    pass

class HolidayConnectionError(HolidayAPIError):
    """Fehler bei der Verbindung zur API"""
    pass

class HolidayDataError(HolidayAPIError):
    """Fehler in den empfangenen Daten"""
    pass

class HolidayManager:
    FERIEN_API_URL = "https://ferien-api.de/api/v1/holidays/"
    FEIERTAGE_API_URL = "https://feiertage-api.de/api/"
    TIMEOUT = 10  # Timeout in Sekunden
    
    def __init__(self, db, state: str = "NW"):
        self.db = db
        self.state = state
        self.logger = logging.getLogger(__name__)
        
    def update_all(self, year: int) -> None:
        """
        Aktualisiert sowohl Ferien als auch Feiertage für das angegebene Jahr.
        
        Raises:
            HolidayAPIError: Wenn beide APIs nicht erreichbar sind
            HolidayDataError: Wenn bei beiden APIs Datenfehler auftreten
        """
        errors = []
        
        try:
            self.db.holidays.clear_public_by_year(year, self.state)
            
            # Versuche beide APIs zu aktualisieren
            try:
                self.update_vacation_days(year)
            except Exception as e:
                self.logger.error(f"Fehler bei Ferien-Update: {str(e)}")
                errors.append(("Ferien", e))
                
            try:
                self.update_public_holidays(year)
            except Exception as e:
                self.logger.error(f"Fehler bei Feiertage-Update: {str(e)}")
                errors.append(("Feiertage", e))
                
            # Wenn beide Updates fehlgeschlagen sind
            if len(errors) == 2:
                error_msg = "\n".join([f"{src}: {str(err)}" for src, err in errors])
                raise HolidayAPIError(f"Beide APIs nicht erreichbar:\n{error_msg}")

            self.db.holidays.update_lesson_status_for_holidays()
                
        except Exception as e:
            self.logger.error(f"Kritischer Fehler beim Update: {str(e)}")
            raise
        
    def update_vacation_days(self, year: int) -> None:
        """
        Holt Ferientage von der Ferien-API.
        
        Raises:
            HolidayConnectionError: Bei Verbindungsproblemen
            HolidayDataError: Bei Problemen mit den empfangenen Daten
        """
        try:
            url = f"{self.FERIEN_API_URL}{self.state}/{year}"
            response = requests.get(url, timeout=self.TIMEOUT)
            response.raise_for_status()
            
            try:
                vacations = response.json()
            except ValueError as e:
                raise HolidayDataError(f"Ungültige JSON-Daten von Ferien-API: {str(e)}")
            
            if not isinstance(vacations, list):
                raise HolidayDataError("Unerwartetes Datenformat von Ferien-API")
            
            for vacation in vacations:
                try:
                    start_date = datetime.strptime(vacation['start'], "%Y-%m-%d")
                    end_date = datetime.strptime(vacation['end'], "%Y-%m-%d")
                    name = vacation.get('name')
                    
                    if not name:
                        self.logger.warning(f"Ferien ohne Namen gefunden: {vacation}")
                        continue
                        
                    current_date = start_date
                    while current_date <= end_date:
                        self.db.holidays.add_public(
                            date=current_date.strftime("%Y-%m-%d"),
                            name=name,
                            type='vacation_day',
                            state=self.state,
                            year=year
                        )
                        current_date += timedelta(days=1)
                        
                except KeyError as e:
                    self.logger.warning(f"Fehlende Ferien-Daten: {str(e)}")
                except ValueError as e:
                    self.logger.warning(f"Ungültiges Datum in Ferien-Daten: {str(e)}")
                    
        except Timeout:
            raise HolidayConnectionError("Zeitüberschreitung bei Ferien-API")
        except ConnectionError:
            raise HolidayConnectionError("Keine Verbindung zur Ferien-API möglich")
        except HTTPError as e:
            raise HolidayConnectionError(f"HTTP-Fehler bei Ferien-API: {str(e)}")
        except RequestException as e:
            raise HolidayConnectionError(f"Fehler bei Ferien-API-Anfrage: {str(e)}")
            
    def update_public_holidays(self, year: int) -> None:
        """
        Holt Feiertage von der Feiertage-API.
        
        Raises:
            HolidayConnectionError: Bei Verbindungsproblemen
            HolidayDataError: Bei Problemen mit den empfangenen Daten
        """
        try:
            params = {
                'jahr': year,
                'nur_land': self.state
            }
            response = requests.get(
                self.FEIERTAGE_API_URL, 
                params=params,
                timeout=self.TIMEOUT
            )
            response.raise_for_status()
            
            try:
                holidays = response.json()
            except ValueError as e:
                raise HolidayDataError(f"Ungültige JSON-Daten von Feiertage-API: {str(e)}")
            
            if not isinstance(holidays, dict):
                raise HolidayDataError("Unerwartetes Datenformat von Feiertage-API")
            
            for name, data in holidays.items():
                try:
                    if 'datum' not in data:
                        self.logger.warning(f"Feiertag ohne Datum: {name}")
                        continue
                        
                    self.db.holidays.add_public(
                        date=data['datum'],
                        name=name,
                        type='holiday',
                        state=self.state,
                        year=year
                    )
                    
                except KeyError as e:
                    self.logger.warning(f"Fehlende Feiertags-Daten: {str(e)}")
                    
        except Timeout:
            raise HolidayConnectionError("Zeitüberschreitung bei Feiertage-API")
        except ConnectionError:
            raise HolidayConnectionError("Keine Verbindung zur Feiertage-API möglich")
        except HTTPError as e:
            raise HolidayConnectionError(f"HTTP-Fehler bei Feiertage-API: {str(e)}")
        except RequestException as e:
            raise HolidayConnectionError(f"Fehler bei Feiertage-API-Anfrage: {str(e)}")

    def get_holidays_for_week(self, week_start: datetime) -> List[Dict]:
        """Holt alle Feiertage/Ferientage für eine Woche."""
        week_end = week_start + timedelta(days=6)
        return self.db.holidays.get_by_date_range(
            week_start.strftime("%Y-%m-%d"),
            week_end.strftime("%Y-%m-%d")
        )

        # In holiday_manager.py ergänzen:

    def initialize_holidays(self, current_year: Optional[int] = None) -> None:
        """
        Initialisiert die Feiertage/Ferien für das aktuelle und nächste Jahr,
        falls sie noch nicht geladen wurden.
        
        Args:
            current_year: Optional das Jahr, für das initialisiert werden soll.
                        Wenn None, wird das aktuelle Jahr verwendet.
        """
        try:
            if current_year is None:
                current_year = datetime.now().year
                
            # Prüfe welche Jahre bereits geladen sind
            loaded_years = self._get_loaded_years()
            
            # Lade aktuelles Jahr falls nötig
            if current_year not in loaded_years:
                self.update_all(current_year)
                
            # Lade nächstes Jahr falls nötig
            next_year = current_year + 1
            if next_year not in loaded_years:
                self.update_all(next_year)
                
        except HolidayAPIError as e:
            self.logger.error(f"Fehler beim Initialisieren der Feiertage: {str(e)}")
            # Wir lassen den Fehler nicht nach oben propagieren, 
            # da fehlende Feiertage nicht kritisch sind
            
    def _get_loaded_years(self) -> List[int]:
        """Ermittelt welche Jahre bereits in der Datenbank sind."""
        try:
            loaded_holidays = self.db.holidays.get_public_by_year(
                year=datetime.now().year,
                state=self.state
            )
            # Extrahiere die Jahre aus den geladenen Feiertagen
            return list(set(h['year'] for h in loaded_holidays))
        except Exception as e:
            self.logger.error(f"Fehler beim Prüfen der geladenen Jahre: {str(e)}")
            return []