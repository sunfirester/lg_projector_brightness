# LG Projector Settings Integration

A native Home Assistant custom integration to control the **Picture Mode** of an LG Projector (or TV) running WebOS.

While Home Assistant provides an official `webostv` integration, it often lacks dropdown control for deep picture settings. This integration solves that by using LG's native Luna API to bypass UI restrictions and expose these settings as native Home Assistant entities.

## Features

- **Picture Mode Control**: Exposed as a native `Select` entity with options like Eco, Standard, Cinema, Game, Filmmaker, and Vivid.
- **Two-way Sync**: Reads the actual state directly from your projector so the dropdown accurately reflects the active settings.
- **Config Flow**: No more `input_text` hacks. Pairing is natively handled through the Home Assistant UI, with secure internal key storage.

## Installation via HACS

1. In Home Assistant, go to **HACS** > **Integrations**.
2. Click the three dots in the top right corner and select **Custom repositories**.
3. Paste the URL of this repository: `https://github.com/sunfirester/lg_projector_brightness`.
4. Select **Integration** as the Category and click **Add**.
5. The integration will now appear in HACS. Click on it and select **Download**.
6. Restart Home Assistant.

## Configuration

1. After restarting, go to **Settings** > **Devices & Services**.
2. Click **Add Integration** and search for **LG Projector Settings**.
3. Enter your projector's IP Address.
4. **Important**: When prompted, look at your projector screen and click **Accept** on the pairing request.
5. The setup is complete! You can now add the new Picture Mode entity to your dashboard.

## Usage in Automations

Because these are standard Home Assistant entities, you can control them using the native `select.select_option` services:

**Change Picture Mode**:
```yaml
service: select.select_option
target:
  entity_id: select.lg_projector_picture_mode
data:
  option: cinema
```
