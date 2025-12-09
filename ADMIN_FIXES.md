# Admin Panel Fixes & Enhancements

## 🛠️ Resolved Issues

### 1. JSON Serialization Error (Promotions & Games)
- **Problem**: The admin panel failed to load lists of promotions and games, displaying "JSON not serializable" errors. This was caused by Python `datetime` and `decimal` objects returned directly from the database not being automatically converted to JSON strings/floats.
- **Fix**: Implemented a `serialize_data` helper in `api/admin.py` to automatically convert `date`/`datetime` to ISO strings and `Decimal` to floats. Applied this to `GET /bonos` and `GET /games`.

### 2. Game Management
- **Problem**: Users could not activate/deactivate games, and default games were missing or required manual entry.
- **Fix**:
    - **Frontend**: Added "Activar/Desactivar" toggle buttons to `admin-juegos.html`.
    - **Backend**: Added `PUT /games/{id_juego}/status` endpoint.
    - **Data**: Created `seed_games.py` script to automatically register standard games (Ruleta, Blackjack, Slot) if missing.

### 3. User Reactivation
- **Problem**: Users could be blocked but not reactivated (checkbox behavior ambiguity).
- **Fix**: Updated `api_update_user_profile` to strictly handle the `activo` field as a string comparison (`activo.lower() == 'true'`), preventing frontend boolean/string mismatches.

## 📄 Files Modified
- `api/admin.py`: Added serializer, updated endpoints.
- `templates/admin-juegos.html`: Added toggle UI logic.
- `seed_games.py`: Created seeding script.

## ✅ Verification Steps
1. **Promotions**: Go to "Promociones" tab. The list should now load without error. Creating a new promotion should work.
2. **Games**: Go to "Juegos". Default games should appear. Click "Desactivar"/"Activar" to toggle status.
3. **Users**: Go to a user profile. Click "Bloqueada" -> Save. Click "Activa" -> Save. Verify status changes persist.
