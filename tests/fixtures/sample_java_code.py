"""
Sample Java code for testing GraphRAG functionality.
Self-contained test data that doesn't require external repositories.
"""

# Adapter Pattern Example
ADAPTER_PATTERN_CODE = """
// FishingBoat.java
public interface RowingBoat {
    void row();
}

// FishingBoat.java
public class FishingBoat {
    private static final Logger LOGGER = LoggerFactory.getLogger(FishingBoat.class);
    
    public void sail() {
        LOGGER.info("The fishing boat is sailing");
    }
}

// FishingBoatAdapter.java
public class FishingBoatAdapter implements RowingBoat {
    private FishingBoat boat;

    public FishingBoatAdapter() {
        boat = new FishingBoat();
    }

    @Override
    public void row() {
        boat.sail();
    }
}

// Captain.java
public class Captain {
    private RowingBoat rowingBoat;

    public Captain(RowingBoat rowingBoat) {
        this.rowingBoat = rowingBoat;
    }

    public void row() {
        rowingBoat.row();
    }
}
"""

# Factory Pattern Example
FACTORY_PATTERN_CODE = """
// Blacksmith.java
public interface Blacksmith {
    Weapon manufactureWeapon(WeaponType weaponType);
}

// WeaponType.java
public enum WeaponType {
    SHORT_SWORD("short sword"),
    SPEAR("spear"),
    AXE("axe");

    private final String title;

    WeaponType(String title) {
        this.title = title;
    }

    @Override
    public String toString() {
        return title;
    }
}

// ElfBlacksmith.java
public class ElfBlacksmith implements Blacksmith {
    public Weapon manufactureWeapon(WeaponType weaponType) {
        return ELFARSENAL.get(weaponType);
    }
}

// OrcBlacksmith.java
public class OrcBlacksmith implements Blacksmith {
    public Weapon manufactureWeapon(WeaponType weaponType) {
        return ORCARSENAL.get(weaponType);
    }
}
"""

# Observer Pattern Example
OBSERVER_PATTERN_CODE = """
// Observer.java
public interface Observer {
    void handle(Event e);
}

// Observable.java
public abstract class Observable {
    private final List<Observer> observers;

    public Observable() {
        this.observers = new ArrayList<>();
    }

    public void addObserver(Observer observer) {
        observers.add(observer);
    }

    public void removeObserver(Observer observer) {
        observers.remove(observer);
    }

    protected void notifyObservers(Event event) {
        for (Observer observer : observers) {
            observer.handle(event);
        }
    }
}

// Weather.java
public class Weather extends Observable {
    private WeatherType currentWeather;

    public void timePasses() {
        WeatherType[] enumValues = WeatherType.values();
        currentWeather = enumValues[(currentWeather.ordinal() + 1) % enumValues.length];
        notifyObservers(new WeatherEvent(currentWeather));
    }
}
"""

# Complete Java project structure for testing
SAMPLE_JAVA_FILES = {
    "src/main/java/adapter/FishingBoat.java": """
package adapter;

import java.util.logging.Logger;

public class FishingBoat {
    private static final Logger LOGGER = Logger.getLogger(FishingBoat.class.getName());
    
    public void sail() {
        LOGGER.info("The fishing boat is sailing");
    }
    
    public void hook() {
        LOGGER.info("The fishing boat is hooking");
    }
}
""",
    
    "src/main/java/adapter/RowingBoat.java": """
package adapter;

public interface RowingBoat {
    void row();
}
""",
    
    "src/main/java/adapter/FishingBoatAdapter.java": """
package adapter;

public class FishingBoatAdapter implements RowingBoat {
    private FishingBoat boat;

    public FishingBoatAdapter() {
        boat = new FishingBoat();
    }

    @Override
    public void row() {
        boat.sail();
    }
}
""",
    
    "src/main/java/factory/Blacksmith.java": """
package factory;

public interface Blacksmith {
    Weapon manufactureWeapon(WeaponType weaponType);
}
""",
    
    "src/main/java/factory/ElfBlacksmith.java": """
package factory;

public class ElfBlacksmith implements Blacksmith {
    
    @Override
    public Weapon manufactureWeapon(WeaponType weaponType) {
        switch (weaponType) {
            case SHORT_SWORD:
                return new ElfWeapon(WeaponType.SHORT_SWORD);
            case SPEAR:
                return new ElfWeapon(WeaponType.SPEAR);
            default:
                throw new IllegalArgumentException("Unknown weapon type");
        }
    }
}
""",
    
    "src/main/java/observer/Weather.java": """
package observer;

import java.util.ArrayList;
import java.util.List;

public class Weather {
    private WeatherType currentWeather;
    private final List<WeatherObserver> observers;

    public Weather() {
        observers = new ArrayList<>();
        currentWeather = WeatherType.SUNNY;
    }

    public void addObserver(WeatherObserver observer) {
        observers.add(observer);
    }

    public void removeObserver(WeatherObserver observer) {
        observers.remove(observer);
    }

    public void timePasses() {
        WeatherType[] enumValues = WeatherType.values();
        currentWeather = enumValues[(currentWeather.ordinal() + 1) % enumValues.length];
        notifyObservers();
    }

    private void notifyObservers() {
        for (WeatherObserver observer : observers) {
            observer.update(currentWeather);
        }
    }
}
"""
}

def get_sample_code_files():
    """Get sample Java files for testing"""
    return SAMPLE_JAVA_FILES

def get_pattern_examples():
    """Get design pattern code examples"""
    return {
        "adapter": ADAPTER_PATTERN_CODE,
        "factory": FACTORY_PATTERN_CODE,
        "observer": OBSERVER_PATTERN_CODE
    } 