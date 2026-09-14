# Sirius Core API — External Interface Reference

> **Version**: 4.0.0  
> **Architecture**: Service-based (core_api_node)  
> **Last Updated**: 2026-04-17

---

## 1.Overview

The Sirius Core API is the unified external interface layer for the quadruped robot Sirius, running on the robot itself. External programs can access the fully equivalent functionality set through either the **HTTP REST** or **WebSocket** protocols; in addition, an independent **MJPEG video stream** port is provided.

| Agreement | Port | Explanation |
|------|------|------|
| HTTP REST | `8088` | Classic RESTful requests/responses, suitable for one-time calls |
| WebSocket | `8765` | JSON message-driven, supports server-side event streaming, suitable for real-time monitoring |
| MJPEG Stream | `8080` | Path `/video_stream`, continuous MJPEG frame streaming |

Connection address example (assuming the robot's IP is `192.168.1.100`):

```
HTTP:       http://192.168.1.100:8088/api/v1/system/ping
WebSocket:  ws://192.168.1.100:8765
MJPEG:      http://192.168.1.100:8080/video_stream
```

---

## 2.General Agreement 

### 2.1 HTTP Request 
- All API paths start with `/api/v1/`
- The request body for POST requests is `application/json` (some file upload interfaces also support `multipart/form-data`)
- Two JSON body styles are supported (automatically compatible):
- **Flat style**: `{ "enabled": true }`
- **Data nested style**: `{ "data": { "enabled": true } }`

### 2.2 HTTP Unified Response Format

```json
{
  "success": true,
  "code": "ok",
  "message": "Success",
  "data": { ... }
}
```


| Field | Type | Description | 
|------|------|------|
| `success` | `boolean` | Whether the request was successful |
| `code` | `string` | Result code (refer to the table below) |
| `message` | `string` | Human-readable description |
| `data` | `object` | Business data | 
| `details` | `object?` | Optional Supplementary Details |

### 2.3 WebSocket Connection 

During the connection process, the calling party's identity can be identified through the query parameter (for event filtering): 

```
ws://192.168.1.100:8765?audience=script
```

Possible values for `audience`: `web`, `script`, `ai`, `unknown` (default). Non-web identities will not receive special events such as internal factory tests. 
After the connection is successful, the server automatically sends the `connection_info` event:

```json
{
  "type": "event",
  "event_type": "connection_info",
  "timestamp": "2026-04-08T12:00:00.000Z",
  "data": {
    "client_id": 1,
    "status": "connected",
    "server_info": {
      "name": "Sirius Core API",
      "version": "4.0.0",
      "architecture": "Service-based",
      "capabilities": ["play_motion", "status_monitoring", "factory_test", "ota_update"]
    }
  }
}
```

Maximum concurrent connection number：**10**。

### 2.4 WebSocket Request Format

```json
{
  "type": "request",
  "request_id": "uuid-or-any-unique-string",
  "request_type": "BATTERY_GET_STATUS",
  "data": {}
}
```

| Field | Type | Required | Description | 
|------|------|------|------|
| `type` | `string` | Yes | Fixed as `"request"` |
| `request_id` | `string` | Yes | Unique identifier for matching the response |
| `request_type` | `string` | Yes | Interface identifier (refer to each service chapter) |
| `data` | `object` | No | Request parameters. Can be omitted or passed as `{}` when no parameters are present |

### 2.5 WebSocket Response format

```json
{
  "type": "response",
  "request_id": "uuid-or-any-unique-string",
  "success": true,
  "code": "ok",
  "message": "Success",
  "timestamp": "2026-04-08T12:00:00.000Z",
  "data": { ... }
}
```

Include an additional `"error"` field when there is a failure (the same as `message`). 

### 2.6 WebSocket Push Event Format

```json
{
  "type": "event",
  "event_type": "battery-status",
  "timestamp": "2026-04-08T12:00:00.000Z",
  "data": { ... }
}
```

### 2.7 WebSocket Heartbeat

Support two heartbeat mechanisms: 
Application Layer Heartbeat (Recommended):

```json
{"type": "heartbeat", "heartbeat_type": "ping"}
→ {"type": "heartbeat", "heartbeat_type": "pong", "timestamp": "..."}
```

**Ping/Pong Message**：

```json
{"type": "ping", "request_id": "optional-id"}
→ {"type": "pong", "request_id": "optional-id", "timestamp": "..."}
```

The server sends protocol-level pings every 30 seconds. If there is no pong response for more than 60 seconds, the connection will be disconnected.

### 2.8 Result Code Reference Table 

| code | HTTP Status | Explanation | 
|------|-------------|------|
| `ok` | 200 | Success |
| `invalid_request` | 400 | Incorrect request format or missing required fields |
| `invalid_argument` | 400 | Illegal parameter values (type error or out of range) |
| `not_found` | 404 | Resource not found |
| `conflict` | 409 | Resource conflict (e.g., file already exists) |
| `service_unavailable` | 503 | Backend service unavailable (ROS dependencies not ready) |
| `timeout` | 504 | Operation timed out |
| `internal_error` | 500 | Internal error |

---

## 3.System 

### 3.1 Health Checkups

| | |
|---|---|
| **HTTP** | `GET /api/v1/system/ping` |
| **WS** | — |
| **Parameter** | None |

**响应 data**：`{}`

---

### 3.2 Interface capability discovery

| | |
|---|---|
| **HTTP** | `GET /api/v1/openapi-map` |
| **WS** | — |
| **Query Parameters** | `audience` (Optional) - When set to 'ai', only the AI-enabled interfaces will be returned.

**Response data**: Returns an array of all registered routes, with each item containing information such as method, path, service, summary, and availability.

---

## 4.BatteryService 

### 4.1 Obtain the battery status

| | |
|---|---|
| **HTTP** | `GET /api/v1/battery/status` |
| **WS request_type** | `BATTERY_GET_STATUS` |
| **Parameter** | None |

### 4.2 Obtain the charging status

| | |
|---|---|
| **HTTP** | `GET /api/v1/battery/charging` |
| **WS request_type** | — |
| **Parameter** | None |

### 4.3 Push Notifications

| event_type | Trigger condition | Data example | 
|---|---|---|
| `battery-status` | Periodic push of battery data when it changes | `{"voltage": 12.3, "percentage": 85, "charging": false, ...}` |

---

## 5. VisionService

### 5.1 Obtain face detection data

| | |
|---|---|
| **HTTP** | `GET /api/v1/vision/faces` |
| **WS request_type** | `VISION_GET_FACES` |
| **Parameter** | None |

**Response data**：`{"faces": [...], "count": N}`

Return when no face is detected `success: false`（`not_found`）。

### 5.2 Obtain gesture recognition data

| | |
|---|---|
| **HTTP** | `GET /api/v1/vision/gestures` |
| **WS request_type** | `VISION_GET_GESTURES` |
| **Parameter** | None |

**Response data**：`{"gestures": [...], "count": N}`

Return an empty array when there is no data or the data is expired (> 2 seconds)：`{"gestures": [], "count": 0}`，`success: true`。

### 5.3 Obtain object detection data

| | |
|---|---|
| **HTTP** | `GET /api/v1/vision/objects` |
| **WS request_type** | `VISION_GET_OBJECTS` |
| **Parameter** | None |

**Response data**：`{"objects": [...], "count": N}`

It always returns an empty array at present：`{"objects": [], "count": 0}`，`success: true`。

### 5.4 Enable/Disable Detection Stream

| | |
|---|---|
| **HTTP** | `POST /api/v1/vision/detection` |
| **WS request_type** | `VISION_SET_DETECTION` |

| Parameter | Type | Required | Default Value | Description |
 |------|------|------|--------|------|
| `enabled` | `boolean` | No | `true` | Whether visual detection is enabled |

### 5.5 Enable/Disable Face Tracking

| | |
|---|---|
| **HTTP** | `POST /api/v1/vision/face-tracking` |
| **WS request_type** | `VISION_SET_FACE_TRACKING` |

| Parameter | Type | Required | Default Value | Description |
|------|------|------|--------|------|
| `enabled` | `boolean` | No | `true` | Whether to enable face tracking |

### 5.6 Push event 

| event_type | Trigger condition | Data description | 
|---|---|---|
| `vision-detection` | When a face/gesture/object is detected | Includes arrays of faces, gestures, and objects |

---

## 6. MotorService 

### 6.1 Obtain the comprehensive status of the motor

| | |
|---|---|
| **HTTP** | `GET /api/v1/motor/status` |
| **WS request_type** | `MOTOR_GET_STATUS` |
| **Parameter** | None |

### 6.2 Obtain the temperature of the motor

| | |
|---|---|
| **HTTP** | `GET /api/v1/motor/temperature` |
| **WS request_type** | `MOTOR_GET_TEMPERATURE` |
| **Parameter** | None |

### 6.3 Obtain motor mode

| | |
|---|---|
| **HTTP** | `GET /api/v1/motor/mode` |
| **WS request_type** | `MOTOR_GET_MODE` |
| **Parameter** | None |

### 6.4 Set the motor torque

| | |
|---|---|
| **HTTP** | `POST /api/v1/motor/torque` |
| **WS request_type** | `MOTOR_SET_TORQUE` |

| Parameter | Type | Required | Range | Description |
|------|------|------|----------|------|
| `torque` | `uint16` | Yes | 0–2047 | Position loop target torque valve (write to servo reg 44-45) |

> **Note**: Here, "torque" refers to the upper limit of torque sent to the position loop (valve) rather than the steady-state output torque. The actual steady-state output power is dynamically determined by the PID based on the position error. To monitor the actual output level, please subscribe to the `motor-load` event in §6.7.

### 6.5 Set the motor mode

| | |
|---|---|
| **HTTP** | `POST /api/v1/motor/mode` |
| **WS request_type** | `MOTOR_SET_MODE` |

| Parameter | Type | Required | Default Value | Description |
|------|------|------|--------|------|
| `mode` | `int8` | yes | — | 0=normal, 1=gait, 2=custom |
| `acceleration_limit` | `uint8` | No | `254` | Acceleration limit |

### 6.6 Enable/Disable Thermal Protection

| | |
|---|---|
| **HTTP** | `POST /api/v1/motor/thermal-protection` |
| **WS request_type** | `MOTOR_SET_THERMAL_PROTECTION` |

| Parameter | Type | Required | Default Value | Description |
|------|------|------|--------|------|
| `enabled` | `boolean` | No | `true` | Whether to enable thermal protection |

> **Alias of Legacy**: WS is also accepted `enable_thermal_protection`。

### 6.7 Push Notifications

| event_type | Trigger condition | Data description |
|---|---|---|
| `motor-temperature` | When the temperature data changes | Temperature values of each motor |
| `motion-mode-changed` | When switching between motor modes | New mode information |
| `motor-load` | Periodic push every second | 14-channel motor real-time `Present_Load` (Pulse Width Modulation duty cycle ‰, without sign bit), can be used for stall/high-voltage monitoring |

**`motor-load` data structure**：

```json
{
  "loads": [12, -34, 820, 15, -8, 910, 5, 10, 12, 8, -3, 6, 0, 2],
  "unit": "pwm_permille",
  "range": { "min": -1000, "max": 1000 },
  "timestamp": 1713350400000
}
```

| Field | Type | Description |
|------|------|------|
| `loads` | `int16[14]` | The `Present_Load` value of the road motor, with a sign. In array order：`FL hip, FL thigh, FL shank, FR hip, FR thigh, FR shank, BL hip, BL thigh, BL shank, BR hip, BR thigh, BR shank, Head yaw, Head pitch` |
| `unit` | `string` | Fixed as `"pwm_permille"` (PWM duty cycle in thousandths) |
| `range` | `object` | Physical quantity range, fixed `-1000 ~ +1000`（±100% PWM） |
| `timestamp` | `int64` | Unix epoch Microsecond timestamp |

**Regarding the meaning of the numbers**：

- `loads[i]` represents the **percentage duty cycle** (‰) of the current output of the servo position loop PID. The sign indicates the direction of force application, and the **absolute value** reflects the force intensity.
- Saturation = `|loads[i]| / 1000`. Empirical threshold: `< 20%` for idle/light load, `20% ~ 60%` for medium load, `≥ 60%` for approaching PWM saturation (potential stall).
- It is **not equal** to the `torque` value issued in §6.4. `torque` is the "upper limit of the valve" (0–2047), while `loads` is the "current actual opening degree" (-1000 ~ +1000 ‰). Even if `torque = 2047`, the valve is fully open, but `loads` will only increase when the mechanical load increases.
---

## 7. MaterialService — Material Management

### 7.1 Upload materials (optional playback)

| | |
|---|---|
| **HTTP** | `POST /api/v1/material/upload` |
| **WS request_type** | `MATERIAL_UPLOAD` |

Support two types of upload methods:

**Method One：JSON + Base64**

| Parameter | Type | Required | Default Value | Description |
|------|------|------|--------|------|
| `filename` | `string` | Yes | — | File name (including extension) |
| `content` | `string` | Yes | — | Base64 encoded file content |
| `upload_only` | `boolean` | No | `false` | `true` = Only upload, no playback |

**Method two：multipart/form-data**（Only HTTP）

| Form Field | Description |
|----------|------|
| `file` | Binary file |
| `filename` | Optional, overrides the file name |
| `upload_only` | Optional, `"true"` indicates only uploading |

> **Alias of Legacy**: WS also accepts `material_upload`.

### 7.2 Stop playing the materials

| | |
|---|---|
| **HTTP** | `POST /api/v1/material/stop` |
| **WS request_type** | `MATERIAL_STOP` |

| Parameter | Type | Required | Default Value | Description |
|------|------|------|--------|------|
| `type` | `string` | No | `"all"` | Stop type (either `"all"` or specified channel) |

> **Legacy Alias: **WS also accepts `material_stop`.

### 7.3 Sequential playback

| | |
|---|---|
| **HTTP** | `POST /api/v1/material/combo-play` |
| **WS request_type** | `MATERIAL_COMBO_PLAY` |

| Parameter | Type | Required | Default Value | Description |
|------|------|------|--------|------|
| `led_file` | `string` | No | `""` | Name of the LED animation file |
| `motion_file` | `string` | No | `""` | Name of the action file |
| `ui_file` | `string` | No | `""` | Name of the UI animation file |
| `wav_file` | `string` | No | `""` | Name of the audio file |

> **Legacy Alias**: WS also accepts `material_combo_play`.

### 7.4 Save the materials to a subdirectory

| | |
|---|---|
| **HTTP** | `POST /api/v1/material/save` |
| **WS request_type** | `MATERIAL_SAVE` |

| Parameter | Type | Required | Description |
|------|------|------|------|
| `filename` | `string` | Yes | File Name |
| `subdir` | `string` || Subdirectory name, case-insensitive. Legal values:`led`、`motion`、`ui`、`wav` |
| `content` | `string` | Yes | The content of the file encoded in Base64 |

> `subdir` The input can be in either uppercase or lowercase (e.g. `"led"`, `"Led"`, `"LED"` are all acceptable). The server will uniformly standardize it as `Led`/`Motion`/`UI`/`Wav`. The response `data.subdir` will return the standardized name.

HTTP simultaneously supports multipart (form fields)：`file`, `filename`, `subdir`）。

> **Alias of Legacy**: WS also accepts `material_save`.

### 7.5 List local materials

| | |
|---|---|
| **HTTP** | `GET /api/v1/material/local-list` |
| **WS request_type** | `MATERIAL_LIST_LOCAL` |

| Parameter | Type | Required | Default Value | Description |
|------|------|------|--------|------|
| `category` | `string` | No | "all" | Filtering category. Legal values：`all`、`actions`、`audio`、`gif` |

HTTP transmits through Query parameters：`?category=actions`。

> **Alternative Name for Legacy**: WS is also accepted `material_list_local`。

### 7.6 Download materials from the cloud

| | |
|---|---|
| **HTTP** | `POST /api/v1/material/cloud-download` |
| **WS request_type** | `MATERIAL_DOWNLOAD_CLOUD` |

| Parameter | Type | Required | Description |
|------|------|------|------|
| `url` | `string` | Yes | Download URL |
| `category` | `string` | Yes | Material category |
| `filename` | `string` | Yes | Saved file name |

> **Alias of Legacy**: WS also accepts `material_download_cloud`.

### 7.7 Push event 

| event_type | Trigger condition | Data description | 
|---|---|---|
| `action-result` | When the media playback is completed or encounters an error | Includes playback result information | 
---

## 8. BehaviorService — Behavior Control 

### 8.1 Pause/Resume Autonomous Behavior

| | |
|---|---|
| **HTTP** | `POST /api/v1/behavior/pause` |
| **WS request_type** | `BEHAVIOR_SET_PAUSE` |

| Parameter | Type | Required | Default Value | Description |
|------|------|------|--------|------|
| `paused` | `boolean` | No | `true` | `true` = Pause, `false` = Resume |

### 8.2 Enable/Disable Random Actions

| | |
|---|---|
| **HTTP** | `POST /api/v1/behavior/random-action` |
| **WS request_type** | `BEHAVIOR_SET_RANDOM_ACTION` |

| Parameter | Type | Required | Default Value | Description |
|------|------|------|--------|------|
| `enabled` | `boolean` | No | `true` | Whether to enable random actions |

### 8.3 Enable/Disable the orchestration mode

| | |
|---|---|
| **HTTP** | `POST /api/v1/behavior/orchestration-mode` |
| **WS request_type** | `BEHAVIOR_SET_ORCHESTRATION_MODE` |

| Parameter | Type | Required | Default Value | Description |
|------|------|------|--------|------|
| `enabled` | `boolean` | No | `true` | Whether to enable orchestration mode |

### 8.4 Reset the behavior state

| | |
|---|---|
| **HTTP** | — |
| **WS request_type** | `reset_action` |

> Specific for WS. Calls the BehaviorService to reset the behavior state (different from §13.3 `ACTION_STOP_ALL` which cancels all action targets).

**Note**: The `reset_action` and `ACTION_STOP_ALL` routes are directed to different services and their behaviors are not equivalent. If you need to stop all actions, please use §13.3's `ACTION_STOP_ALL`.

### 8.5 推送事件

| event_type | Trigger condition | Data description |
|---|---|---|
| `behavior-status` | When the behavior state changes | Current behavior state snapshot |

---

## 9. UserDataService - User Data 

### 9.1 Retrieving/Setting the Theme 

| | |
|---|---|
| **HTTP GET** | `GET /api/v1/user/theme` |
| **HTTP POST** | `POST /api/v1/user/theme` |
| **WS GET** | `USER_GET_THEME` |
| **WS SET** | `USER_SET_THEME` |

**SET Parameters** 

| Parameter | Type | Required | Range | Description | 
|------|------|------|----------|------|
| `theme_id` | `uint8` | Yes | 1–5 | Theme ID | 

### 9.2 Obtaining/Setting MBTI 

| | |
|---|---|
| **HTTP GET** | `GET /api/v1/user/mbti` |
| **HTTP POST** | `POST /api/v1/user/mbti` |
| **WS GET** | `USER_GET_MBTI` |
| **WS SET** | `USER_SET_MBTI` |

**SET Parameters** 

| Parameter | Type | Required | Range | Description | 
|------|------|------|----------|------|
| `ei_value` | `uint8` | Yes | 0–100 | E/I Dimension Value |
| `sn_value` | `uint8` | Yes | 0–100 | S/N Dimension Value |
| `tf_value` | `uint8` | Yes | 0–100 | T/F Dimension Value |
| `jp_value` | `uint8` | Yes | 0–100 | J/P Dimension Value | 

### 9.3 Obtaining/Setting Robot Mode 

| | |
|---|---|
| **HTTP GET** | `GET /api/v1/user/robot-mode` |
| **HTTP POST** | `POST /api/v1/user/robot-mode` |
| **WS GET** | `USER_GET_ROBOT_MODE` |
| **WS SET** | `USER_SET_ROBOT_MODE` |

**SET Parameters** 

| Parameter | Type | Required | Value | Description | 
|------|------|------|------|------|
| `robot_mode` | `string` | Yes | `"desktop"` \| `"ground"` | Robot operation mode | 

### 9.4 Obtain the status of the opening ceremony 

| | |
|---|---|
| **HTTP** | `GET /api/v1/user/ritual-status` |
| **WS request_type** | `USER_GET_RITUAL_STATUS` |
| **Parameter** | None | 

### 9.5 The opening ceremony of the marking process has been completed. 

| | |
|---|---|
| **HTTP** | `POST /api/v1/user/ritual-complete` |
| **WS request_type** | `USER_SET_RITUAL_COMPLETE` |

| Parameter | Type | Required | Default Value | Description |
|------|------|------|--------|------|
| `force_reset` | `boolean` | No | `false` | Force reset of ritual status | 

### 9.6 Obtaining Node Parameters 

| | |
|---|---|
| **HTTP** | `GET /api/v1/user/node-parameter` |
| **WS request_type** | `USER_GET_NODE_PARAMETER` |

**HTTP Query Parameters**: `?` node_name=xxx&parameter_name=yyy`

**WS data parameters** 

| Parameter | Type | Required | Description | 
|------|------|------|------|
| `node_name` | `string` | Yes | ROS node name |
| `parameter_name` | `string` | Yes (when single) | Parameter name |
| `parameter_names` | `string[]` | Yes (when batch) | Array of parameter names (supported by WS) |

### 9.7 Set parameters for a single node 

| | |
|---|---|
| **HTTP** | `POST /api/v1/user/node-parameter` |
| **WS request_type** | `USER_SET_NODE_PARAMETER` |

| Parameter | Type | Required | Description | 
|------|------|------|------|
| `node_name` | `string` | Yes | ROS node name |
| `parameter_name` | `string` | Yes | Parameter name |
| `parameter_value` | `any` | Yes | Parameter value (bool/int/double/string) | 

### 9.8 Batch Setting of Node Parameters 

| | |
|---|---|
| **HTTP** | `POST /api/v1/user/node-parameters` |
| **WS request_type** | `USER_SET_NODE_PARAMETERS` |

| Parameter | Type | Required | Description | 
|------|------|------|------|
| `node_name` | `string` | Yes | ROS node name |
| `parameters` | `object` | Yes | Key-value pair { "param_a": value_a, "param_b": value_b } | 

### 9.9 Push Notifications 

| event_type | Trigger condition | Data description |
|---|---|---|
| `robot_mode_changed` | When the robot mode is changed | `{"robot_mode": "desktop" | "ground"}` |
| `parameter_changed` | When the `/gait_generation_trot_node` parameter is changed | `{"node_name": "..."` , "parameter_name": "..." , "parameter_value": ... ` | 
---

## 10.EmotionService — Emotion 

### 10.1 Retrieving Emotional History 

| | |
|---|---|
| **HTTP** | `GET /api/v1/emotion/history` |
| **WS request_type** | `EMOTION_GET_HISTORY` |

| Parameter | Type | Required | Default Value | Description |
|------|------|------|--------|------|
| `duration_seconds` | `int` | No | `300` | Query the historical data within the last N seconds | 
HTTP uses Query parameters for transmission: `?duration_seconds=300`. 

### 10.2 Setting Emotional State 

| | |
|---|---|
| **HTTP** | `POST /api/v1/emotion/state` |
| **WS request_type** | `EMOTION_SET_STATE` |

| Parameter | Type | Required | Range | Description | 
|------|------|------|----------|------|
| `valence_value` | `float` | Yes | 0–100 | Emotional valence (positive/negative) |
| `arousal_value` | `float` | Yes | 0–100 | Emotional arousal (excitement/calming) | 

### 10.3 Regulating Fullness Perception 

| | |
|---|---|
| **HTTP** | `POST /api/v1/emotion/satiety` |
| **WS request_type** | `EMOTION_ADJUST_SATIETY` |

| Parameter | Type | Required | Range | Description | 
|------|------|------|----------|------|
| `satiety_delta` | `float` | Yes | -100 to 100 | Increase/decrease in satiety level |

### 10.4 Push Notifications 

| event_type | Trigger condition | Data description |
|---|---|---|
| `emotion-update` | When emotional state changes | Includes valence, arousal, emotion_name, satiety, etc. |
| `touch-event` | When a touch/gesture event is detected | Touch event data |
---

## 11. NetworkService — Network 

### 11.1 Scanning Wi-Fi Networks 

| | |
|---|---|
| **HTTP** | `GET /api/v1/network/scan` |
| **WS request_type** | `NETWORK_SCAN` |

| Parameter | Type | Required | Default Value | Description |
|------|------|------|--------|------|
| `force_rescan` | `boolean` | No | `false` | Force re-scanning |
| `scan_timeout` | `int` | No | `10` | Scan timeout (seconds) | 
HTTP transmits via Query parameters: `?force_rescan=true&scan_timeout=15`. 

### 11.2 Connecting to Wi-Fi 

| | |
|---|---|
| **HTTP** | `POST /api/v1/network/connect` |
| **WS request_type** | `NETWORK_CONNECT` |

| Parameter | Type | Required | Default Value | Description |
|------|------|------|--------|------|
| `ssid` | `string` | Yes | — | Wi-Fi Name |
| `password` | `string` | No | `""` | Wi-Fi Password |
| `security_type` | `string` | No | `""` | Security Type |
| `force_reconnect` | `boolean` | No | `false` | Force Reconnect |
| `timeout_seconds` | `int` | No | `30` | Connection Timeout (seconds) | 

### 11.3 Hotspot Control 

| | |
|---|---|
| **HTTP** | `POST /api/v1/network/hotspot` |
| **WS request_type** | `NETWORK_HOTSPOT_CONTROL` |

| Parameter | Type | Required | Default Value | Description |
|------|------|------|--------|------|
| `enable` | `boolean` | Yes | — | Enable/Disable hotspot |
| `ssid` | `string` | No | `""` | Hotspot name |
| `password` | `string` | No | `""` | Hotspot password |
| `timeout_seconds` | `int` | No | `30` | Timeout (seconds) | 

### 11.4 Obtaining Hotspot Status 

| | |
|---|---|
| **HTTP** | `GET /api/v1/network/hotspot/status` |
| **WS request_type** | `NETWORK_GET_HOTSPOT_STATUS` |
| **Parameter** | None |

### 11.5 Retrieving the List of Saved Wi-Fi Networks 

| | |
|---|---|
| **HTTP** | `GET /api/v1/network/saved` |
| **WS request_type** | `NETWORK_GET_SAVED` |
| **Parameter** | None |

> **Alias of Legacy**: WS also accepts `network_get_saved`. 

### 11.6 Forgetting Wi-Fi Network 

| | |
|---|---|
| **HTTP** | `POST /api/v1/network/forget` |
| **WS request_type** | `NETWORK_FORGET` |

| Parameter | Type | Required | Description | 
|------|------|------|------|
| `ssid` | `string` | Yes | The Wi-Fi name to be forgotten | 
> **Alias of Legacy**: WS also accepts `network_forget`. 

### 11.7 Push Notifications 

| event_type | Trigger condition | Data description |
|---|---|---|
| `network-status` | When the network status changes | Current connection information |
| `hotspot-status` | When the hotspot status changes | Status and information of the hotspot switch | 
---

## 12. OTAService — OTA Upgrade 

### 12.1 Check for Updates

| | |
|---|---|
| **HTTP** | `GET /api/v1/ota/check` |
| **WebSocket Request Type** | `OTA_CHECK_UPDATE` || **Parameters** | None |
| **Timeout** | 30 seconds | 

### 12.2 Start Updating 

| | |
|---|---|
| **HTTP** | `POST /api/v1/ota/start` |
| **WebSocket Request Type** | `OTA_START_UPDATE` | 

| Parameter | Type | Required | Default Value | Description |
|------|------|------|--------|------|
| "Automatic Restart" | "Boolean Value" | No | "false" | Whether to automatically restart after update is completed | 

### 12.3 Rollback Updates 

| | |
|---|---|
| **HTTP** | `POST /api/v1/ota/rollback` |
| **WS request_type** | `OTA_ROLLBACK` |
| **Parameter** | None |

### 12.4 Cancel Update 

| | |
|---|---|
| **HTTP** | `POST /api/v1/ota/cancel` |
| **WS request_type** | `OTA_CANCEL` |
| **Parameter** | None |

### 12.5 Obtaining OTA Status and Progress 

| | |
|---|---|
| **HTTP** | `GET /api/v1/ota/status` |
| **WS request_type** | `OTA_GET_STATUS` |
| **Parameter** | None |

### 12.6 Set the OTA server address 

| | |
|---|---|
| **HTTP** | `POST /api/v1/ota/server-url` |
| **WS request_type** | `OTA_SET_SERVER_URL` |

| Parameter | Type | Required | Description | 
|------|------|------|------|
| `url` | `string` | Yes | OTA server URL | 

### 12.7 Obtain OTA Configuration 

| | |
|---|---|
| **HTTP** | `GET /api/v1/ota/config` |
| **WS request_type** | `OTA_GET_CONFIG` |
| **Parameter** | None |

### 12.8 List the OTA versions (specific to WS) 

| | |
|---|---|
| **HTTP** | — |
| **WS request_type** | `OTA_LIST_VERSIONS` |

| Parameter | Type | Required | Default Value | Description |
|------|------|------|--------|------|
| `channel` | `string` | No | `"all"` | Version channel filtering | 

> **Alias of Legacy**: WS also accepts `list_ota_versions`.

### 12.9 Push Notifications 

| event_type | Trigger condition | Data description |
|---|---|---|
| `ota-status` | When the OTA status changes | `{"status": "..."}` |
| `ota-progress` | When the OTA download/install progress is updated | `{"progress": "..."}` |
| `ota_log_update` | OTA log output | `{"message": "..."}` or structured log | 
---

## 13. ActionService - Action Playback 

### 13.1 Playback Action 

| | |
|---|---|
| **HTTP** | `POST /api/v1/action/play` |
| **WS request_type** | `ACTION_PLAY` |

| Parameter | Type | Required | Default Value | Description |
|------|------|------|--------|------|
| `file_path` | `string` | Required | `""` | The complete path of the action file (either `action_name` or `file_path` can be used) |
| `action_name` | `string` | Required | `""` | The name of the action (automatically searched in the `actions` directory) |
| `priority` | `int` | Optional | `1` | Priority |
| `torque` | `int` | Optional | `2047` | Torque value (0–2047) |
| `loop` | `boolean` | Optional | `false` | Whether to loop playback |
| `lottie_file_path` | `string` | Optional | `""` | The path of the Lottie animation file |
| `lottie_x` | `int` | Optional | `-1` | X coordinate of the Lottie animation (0 = centered) |
| `lottie_y` | `int` | Optional | `-1` | Y coordinate of the Lottie animation (0 = centered) |
| `lottie_width` | `int` | Optional | `240` | Width of the Lottie animation |
| `lottie_height` | `int` | Optional | `240` | Height of the Lottie animation |
| `lottie_loop` | `boolean` | Optional | `true` | Whether the Lottie animation is looped |
| `lottie_bg_color` | `int` | Optional | `0x000000` | Background color of the Lottie animation (RGB hex) |
| `lottie_bg_opacity` | `int` | Optional | `255` | Transparency of the Lottie background (0–255) |
| `hide_eye_layer` | `boolean` | Optional | `true` | Whether to hide the eye layer during playback | 

> **Alias of Legacy**: WS also accepts `play_motion`. HTTP also supports `/api/v1/control/action/play` (the old path). 

### 13.2 Stop the current action 

| | |
|---|---|
| **HTTP** | `POST /api/v1/action/stop` |
| **WS request_type** | `ACTION_STOP` |
| **Parameter** | None |

**Idempotent Semantics**: If there is no ongoing action at the moment, it still returns `success: true` and `data.status` as `"idle"`; when an action is cancelled, `data.status` is set to `"canceled"`. 
> **Alias of Legacy**: WS also accepts `cancel_motion`. HTTP also supports `/api/v1/control/action/stop` (the old path). 

### 13.3 Stop all actions 

| | |
|---|---|
| **HTTP** | `POST /api/v1/action/stop-all` |
| **WS request_type** | `ACTION_STOP_ALL` |
| **Parameter** | None |

> **Alias of Legacy**: WS also accepts `stop_all_motions`.

### 13.4 Obtaining the List of Actions 

| | |
|---|---|
| **HTTP** | `GET /api/v1/action/list` |
| **WS request_type** | `ACTION_GET_LIST` |

| Parameter | Type | Required | Default Value | Description |
|------|------|------|--------|------|
| `query` | `string` | Optional | `""` | Search keyword |
| `category` | `string` | Optional | `""` | Filter by category |
| `emotion` | `string` | Optional | `""` | Filter by emotion label |
| `limit` | `int` | Optional | `1000` | Maximum number of returned results | 

HTTP transmits through Query parameters. 

> **Alias of Legacy**: WS also accepts `get_actions`. 

### 13.5 Obtaining Action Metadata 

| | |
|---|---|
| **HTTP** | `GET /api/v1/action/metadata` |
| **WS request_type** | `ACTION_GET_METADATA` |
| **Parameter** | None |

### 13.6 Obtaining Action Status 

| | |
|---|---|
| **HTTP** | `GET /api/v1/action/status` |
| **WS request_type** | `ACTION_GET_STATUS` |
| **Parameter** | None |

> **Alias of Legacy**: WS also accepts `get_status`. 

### 13.7 Push Notifications 

| event_type | Trigger condition | Data description |
|---|---|---|
| `action-progress` | Update on the progress of the action execution | `{"progress": 0.5, "status": "executing", "message": "..." , "current_frame": "..."}`|
| `action-result` | Action execution completed/failed | `{"status": "succeeded"\|"aborted"\|"canceled", "success": bool, "message": "...", "duration": 3.5}` | 
---

## 14. ActionFileService — Action File Management 

### 14.1 Renaming Action File 
| | |
|---|---|
| **HTTP** | `POST /api/v1/action-file/rename` |
| **WS request_type** | `ACTION_FILE_RENAME` |

| Parameter | Type | Required | Description |
|------|------|------|------|
| `old_filename` | `string` | Yes | Original file name |
| `new_filename` | `string` | Yes | New file name | 
The parameters can also be replaced with `from`/`to` instead of `old_filename`/`new_filename`.

**Legacy alias**: WS also accepts `rename_action`. 

### 14.2 Deleting Action Files 

| | |
|---|---|
| **HTTP** | `POST /api/v1/action-file/delete` |
| **WS request_type** | `ACTION_FILE_DELETE` |

| Parameter | Type | Required | Description | 
|------|------|------|------|
| `filename` | `string` | Yes | The file name to be deleted | 

> **Alias of Legacy**: WS also accepts `delete_action`. 

### 14.3 Upload Action File 

| | |
|---|---|
| **HTTP** | `POST /api/v1/action-file/upload` |
| **WS request_type** | `ACTION_FILE_UPLOAD` |

| Parameter | Type | Required | Default Value | Description |
|------|------|------|--------|------|
| `filename` | `string` | Yes | — | File name |
| `content` | `string` | Yes | — | Base64 encoded file content |
| `overwrite` | `boolean` | No | `false` | Whether to overwrite an existing file | 
> **Alias of Legacy**: WS also accepts `upload_action`. 

### 14.4 Downloading Action Files 

| | |
|---|---|
| **HTTP** | `GET /api/v1/action-file/download` |
| **WS request_type** | `ACTION_FILE_DOWNLOAD` |

| Parameter | Type | Required | Description | 
|------|------|------|------|
| `filename` | `string` | Yes | File name | 

HTTP transmits via Query parameters: `?filename=xxx.avi`. 

**Response data**: Contains the `content` field (the file content encoded in Base64). 

> **Alias of Legacy**: WS also accepts `download_action`. 
---

## 15. HardwareControlService — Hardware Control

### 15.1 Audio Recording Control

| | |
|---|---|
| **HTTP** | `POST /api/v1/hardware/audio/record/control` |
| **WS request_type** | — |

| Parameter | Type | Required | Description | 
|------|------|------|------|
| `action` | `string` | Yes | Control instruction (such as "start", "stop", etc.) | 

### 15.2 Audio Recording Status 

| | |
|---|---|
| **HTTP** | `GET /api/v1/hardware/audio/record/status` |
| **WS request_type** | — |
| **Parameter** | None |

### 15.3 Fan Speed Control 

| | |
|---|---|
| **HTTP** | `POST /api/v1/hardware/fan/speed` |
| **WS request_type** | — |

| Parameter | Type | Required | Default Value | Description | 
|------|------|------|--------|------|
| `speed` | `int` | No | `50` | Fan speed percentage | 
---

## 16. LifecycleService — Lifecycle Management 

### 16.1 Obtain the lifecycle status of all nodes 

| | |
|---|---|
| **HTTP** | `GET /api/v1/lifecycle/states` |
| **WS request_type** | `LIFECYCLE_GET_STATES` |
| **Parameter** | None |

> **Alias of Legacy**: WS also accepts `get_lifecycle_states`. 

### 16.2 Set the lifecycle status of nodes 

| | |
|---|---|
| **HTTP** | `POST /api/v1/lifecycle/state` |
| **WS request_type** | `LIFECYCLE_SET_STATE` |

| Parameter | Type | Required | Description | 
|------|------|------|------|
| `node_name` | `string` | Yes | Name of the target node |
| `action` | `string` | Yes | Lifecycle action | 

> **Alias of Legacy**: WS also accepts `set_lifecycle_state`. 

### 16.3 Push Notifications 

| event_type | Trigger condition | Data description | 
|---|---|---|
| `lifecycle_update` | When the node status changes | Information about the node's lifecycle state |
| `system_metrics` | When system metrics are updated | CPU, memory, and other system metrics | 
---

## 17. GaitTrajectoryService — Gait Trajectory 

### 17.1 Query gait trajectory data 
| | |
|---|---|
| **HTTP** | `GET /api/v1/gait-trajectory/query` |
| **WS request_type** | `GAIT_TRAJECTORY_GET` |
| **Parameter** | None |

> **Alias of Legacy**: WS also accepts `get_gait_trajectory`. 

### 17.2 Push Notifications

| event_type | Trigger condition | Data description | 
|---|---|---|
| `gait-trajectory` | When gait data is updated | Real-time trajectory point data | 
---

## 18. SyncService — Multi-device Synchronization 

### 18.1 Scheduling Synchronization Command

| | |
|---|---|
| **HTTP** | `POST /api/v1/sync/execute` |
| **WS request_type** | `SYNC_EXECUTE` |

| Parameter | Type | Required | Default Value | Description |
|------|------|------|--------|------|
| `sync_id` | `string` | No | `""` | Sync task identifier |
| `command_type` | `string` | No | `""` | Command type |
| `scheduled_time_ms` | `int64` | No | `0` | Scheduled execution timestamp (in milliseconds) |
| `payload` | `object` | No | `{}` | Command payload data | 

> **Alias of Legacy**: WS also accepts `sync_execute`. 

### 18.2 Obtaining System Time 

| | |
|---|---|
| **HTTP** | `GET /api/v1/sync/time` |
| **WS request_type** | `SYNC_GET_SYSTEM_TIME` |
| **Parameter** | None | 

> **Alias of Legacy**: WS also accepts `get_system_time`. 

### 18.3 Obtaining the Status of Chrony 

| | |
|---|---|
| **HTTP** | `GET /api/v1/sync/chrony/status` |
| **WS request_type** | `SYNC_GET_CHRONY_STATUS` |
| **Parameter** | None | 

> **Alias of Legacy**: WS also accepts `get_chrony_status`.

### 18.4 Setting the Chrony Role 

| | |
|---|---|
| **HTTP** | `POST /api/v1/sync/chrony/role` |
| **WS request_type** | `SYNC_SET_CHRONY_ROLE` |

| Parameter | Type | Required | Description | 
|------|------|------|------|
| `role` | `string` | Yes | Role (e.g. "master", "client") |
| `master_ip` | `string` | No | IP address of the master node (must be specified for the client role) | 

> **Alias of Legacy**: WS also accepts `set_chrony_role`. 

### 18.5 Performing Stepwise Time Synchronization with Chrony 

| | |
|---|---|
| **HTTP** | `POST /api/v1/sync/chrony/makestep` |
| **WS request_type** | `SYNC_CHRONY_MAKESTEP` |
| **Parameter** | None | 

> **Alias of Legacy**: WS also accepts `execute_chrony_makestep`. 
---

## 19. SensorService — Sensor 

### 19.1 Obtaining TOF Sensor Data 

| | |
|---|---|
| **HTTP** | `GET /api/v1/sensor/tof` |
| **WS request_type** | `SENSOR_GET_TOF` |
| **Parameter** | None | 
> **Alias of Legacy**: WS also accepts `get_tof`. 

### 19.2 Obtaining IMU Sensor Data 

| | |
|---|---|
| **HTTP** | `GET /api/v1/sensor/imu` |
| **WS request_type** | `SENSOR_GET_IMU` |
| **Parameter** | None | 
> **Alias of Legacy**: WS also accepts `get_imu`. 
---

## 20. TransformService — Orientation Transformation 

### 20.1 Obtaining Complete Posture State 

| | |
|---|---|
| **HTTP** | `GET /api/v1/transform/status` |
| **WS request_type** | `TRANSFORM_GET_STATUS` |
| **Parameter** | None | 
**Response Data Structure** 
```json
{
"body": {
"tran_x": 0.0, "tran_y": 0.0, "tran_z": 0.0,
"roll": 0.0, "pitch": 0.0, "yaw": 0.0 },
"head": {
"pitch": 0.0, "yaw": 0.0 },
"foot_points": {
"front_left":  {"x": 0.0, "y": 0.0, "z": 0.0},
"front_right": {"x": 0.0, "y": 0.0, "z": 0.0},
"back_left":   {"x": 0.0, "y": 0.0, "z": 0.0},
"back_right":  {"x": 0.0, "y": 0.0, "z": 0.0} }
}
```

### 20.2 Obtaining/Setting Body Orientation 

| | |
|---|---|
| **HTTP GET** | `GET /api/v1/transform/body` |
| **HTTP POST** | `POST /api/v1/transform/body` |
| **WS GET** | `TRANSFORM_GET_BODY` |
| **WS SET** | `TRANSFORM_SET_BODY` |

**SET Parameters** (all of type `double`, optional, only the fields that need to be modified are passed): 

| Parameter | Description | Alias | 
|------|------|------|
| `tran_x` | X-axis translation | Also accepts `x` |
| `tran_y` | Y-axis translation | Also accepts `y` |
| `tran_z` | Z-axis translation | Also accepts `z` |
| `roll` | Roll angle | — |
| `pitch` | Pitch angle | — |
| `yaw` | Yaw angle | — | 

### 20.3 Obtaining/Setting Head Orientation 

| | |
|---|---|
| **HTTP GET** | `GET /api/v1/transform/head` |
| **HTTP POST** | `POST /api/v1/transform/head` |
| **WS GET** | `TRANSFORM_GET_HEAD` |
| **WS SET** | `TRANSFORM_SET_HEAD` |

**SET Parameters** (all of type `double`, optional): 

| Parameter | Description | Alias | 
|------|------|------|
| `pitch` | Pitch Angle | Also accepts `x` |
| `yaw` | Yaw Angle | Also accepts `y` | 

### 20.4 Retrieving/Setting Foot End Point Position 

| | |
|---|---|
| **HTTP GET** | `GET /api/v1/transform/foot-point/{leg}` |
| **HTTP POST** | `POST /api/v1/transform/foot-point/{leg}` |
| **WS GET** | `TRANSFORM_GET_FOOT_POINT` |
| **WS SET** | `TRANSFORM_SET_FOOT_POINT` |

Path parameters (HTTP): `front-left`, `front-right`, `back-left`, `back-right` 
WS is specified through the `leg` field in the data, and it supports both hyphen and underscore formats: 

| Parameter | Type | Required | Default Value | Description | 
|------|------|------|--------|------|
| `leg` | `string` | Yes | `"front_left"` | Leg identifier |
| `x` | `double` | No | — | X-coordinate |
| `y` | `double` | No | — | Y-coordinate |
| `z` | `double` | No | — | Z-coordinate | 

When using WS SET, the coordinates can be placed in the `data.point` sub-object or directly in the `data` object.

### 20.5 Batch Setting of Complete Posture 

| | |
|---|---|
| **HTTP** | `POST /api/v1/transform/complete` |
| **WS request_type** | `TRANSFORM_SET_COMPLETE` |

Set the body, head and all the terminal points at once. The parameter structure is the same as the 20.1 response format: 

```json
{
"body": {"translation_x": 0.0, "pitch": 5.0},
"head": {"yaw": 10.0},
"foot_points": {
"front_left": {"z": -0.15},
"back_right": {"z": -0.15} }
}
```

Please provide only the part that needs to be modified. 

### 20.6 Attitude Control (Legacy WS Compatibility) 

| | |
|---|---|
| **WS request_type** | `attitude_control` |
| **Description** | The Legacy interface, mapped to TransformService.setAttitudeControlAsync | 

| | |
|---|---|
| **WS request_type** | `pose_control` |
| **Description** | The Legacy interface, mapped to TransformService.setPoseControlAsync | 
---

## 21. GaitService — Gait Movement 

### 21.1 Set Gait Mode 

| | |
|---|---|
| **HTTP** | `POST /api/v1/gait/mode` |
| **WS request_type** | `GAIT_SET_MODE` |

| Parameter | Type | Required | Description | 
|------|------|------|------|
| `mode` | `string` | Yes | Gait mode | 

**Supported mode values**: 
| Mode value | Alias | Description |
|---------|------|------|
| `default` | — | Default standing mode |
| `gait` | `fast`, `fast_run` | Fast gait |
| `slow` | — | Slow gait |
| `walk` | — | Walking gait |
| `precision` | — | Precise gait |
| `climb` | — | Climbing gait |
| `custom` | — | Custom gait | 

> **Alias of Legacy**: WS also accepts `set_motion_mode`. 

### 21.2 Set Gait Speed 

| | |
|---|---|
| **HTTP** | `POST /api/v1/gait/velocity` |
| **WS request_type** | `GAIT_SET_VELOCITY` |

| Parameter | Type | Required | Default Value | Description | 
|------|------|------|--------|------|
| `linear_x` | `double` | No | `0.0` | Front-back speed (positive = forward, negative = backward) |
| `linear_y` | `double` | No | `0.0` | Left-right speed (positive = left movement, negative = right movement) |
| `angular_z` | `double` | No | `0.0` | Rotation speed (positive = left turn, negative = right turn) | 

> **Alias of Legacy**: WS also accepts `gait_control`. 

### 21.3 Directional Movement (Convenient Interface) 

| HTTP Path | WS Request Type | Direction | 
|-----------|-----------------|------|
| `POST /api/v1/gait/move/forward` | `GAIT_MOVE_FORWARD` | Forward |
| `POST /api/v1/gait/move/backward` | `GAIT_MOVE_BACKWARD` | Backward |
| `POST /api/v1/gait/move/left` | `GAIT_MOVE_LEFT` | Left movement |
| `POST /api/v1/gait/move/right` | `GAIT_MOVE_RIGHT` | Right movement |
| `POST /api/v1/gait/move/turn-left` | `GAIT_TURN_LEFT` | Left turn |
| `POST /api/v1/gait/move/turn-right` | `GAIT_TURN_RIGHT` | Right turn | 

| Parameter | Type | Required | Default Value | Description | 
|------|------|------|--------|------|
| `speed` | `double` | No | Linear default value `0.15`, rotation default value `0.5` | Speed value (effective when > 0, uses default value when ≤ 0) | 

### 21.4 Stopping Gait Movement 

| | |
|---|---|
| **HTTP** | `POST /api/v1/gait/stop` |
| **WS request_type** | `GAIT_STOP` |
| **Parameter** | None | 

### 21.5 Stepping Movement (WS-specific, Legacy) 

| | |
|---|---|
| **WS request_type** | `GAIT_STEP_MOVE` |

| Parameter | Type | Required | Default Value | Description | 
|------|------|------|--------|------|
| `linear_x` | `double` | No | `0.0` | Front-back speed |
| `linear_y` | `double` | No | `0.0` | Left-right speed |
| `angular_z` | `double` | No | `0.0` | Rotation speed |
| `steps` | `int` | No | `1` | Number of steps | 
> **Alias of Legacy**: WS also accepts `gait_step_move`. 

### 21.6 Push Notifications 

| event_type | Trigger condition | Data description | 
|---|---|---|
| `gait-mode-changed` | When the gait mode is changed | `{"mode": 0, "mode_name": "default"}` | 
---

## 22. EmotionInteractionService - Emotional Interaction (Specific to WS) 

| | |
|---|---|
| **HTTP** | — |
| **WS request_type** | `EMOTION_INTERACTION` |

> **Alias of Legacy**: WS also accepts `emotion_interaction`. 

The interaction type is determined by the `data.interaction_type` field: 

### 22.1 Feeding 

```json
{
"interaction_type": "feed",
"valence_delta": 20.0,
"arousal_delta": 10.0,
"action_path": "/root/material/actions/stand_default_eatHeartily_brief.avi"
}
```

| Parameter | Type | Required | Default Value | Description | 
|------|------|------|--------|------|
| `interaction_type` | `string` | Yes | — | Fixed as `"feed"` |
| `valence_delta` | `float` | No | `20.0` | Emotional valence change amount |
| `arousal_delta` | `float` | No | `10.0` | Alertness change amount |
| `action_path` | `string` | No | (Built-in default action) | Path of the triggered action file | 

### 22.2 Food Container 

```json
{"interaction_type": "feeding_object", "object_name": "apple"}
```

| Parameter | Type | Required | Description | 
|------|------|------|------|
| `interaction_type` | `string` | Yes | Fixed as `"feeding_object"` |
| `object_name` | `string` | Yes | Name of the object (needs to be registered in the configuration) | 

### 22.3 Adjusting Position 

```json
{"interaction_type": "adjust_position", ...}
```

### 22.4 Gesture Simulation 

```json
{"interaction_type": "gesture_simulation", ...}
```

### 22.5 Object Interaction 

```json
{"interaction_type": "object_interaction", "object_name": "ball"}
```

### 22.6 Performance Skills / Emotional Actions 

```json
{"interaction_type": "performance_skill", "skill_name": "dance"}
{"interaction_type": "emotion_action", "action_name": "happy"}
```

---

## 23. MJPEG Video Stream 

| | |
|---|---|
| **Address** | `http://{robot_ip}:8080/video_stream` |
| **Method** | `GET` |
| **Content-Type** | `multipart/x-mixed-replace; boundary=frame` |

You can directly access the live video frames by visiting the browser or using the `<img>` tag. 
---

## 24. Summary of WebSocket Push Events 

The following lists all the event types that are actively pushed by the server. Once you establish a WebSocket connection, you can receive these events without the need for subscription. 

| event_type | source_service | description | 
|---|---|---|
| `connection_info` | CoreAPINode | Sent upon successful connection |
| `battery-status` | BatteryService | Battery status data |
| `vision-detection` | VisionService | Visual detection results |
| `motor-temperature` | MotorService | Motor temperature data |
| `motor-load` | MotorService | 14-channel motor real-time Present_Load (PWM ‰) |
| `motion-mode-changed` | MotorService | Motor mode change |
| `behavior-status` | BehaviorService | Behavior status change |
| `robot_mode_changed` | UserDataService | Robot mode switch |
| `parameter_changed` | CoreAPINode | Gait node parameter change |
| `emotion-update` | EmotionService | Emotional state update |
| `touch-event` | EmotionService | Touch/Gesture event |
| `network-status` | NetworkService | Network status change |
| `hotspot-status` | NetworkService | Hotspot status change |
| `ota-status` | OTAService | OTA status change |
| `ota-progress` | OTAService | OTA progress update |
| `ota_log_update` | OTAService | OTA log output |
| `action-progress` | ActionService | Action execution progress |
| `action-result` | ActionService / MaterialService | Action/Sample playback result |
| `lifecycle_update` | LifecycleService | Node lifecycle change |
| `system_metrics` | LifecycleService | System resource metrics |
| `gait-trajectory` | GaitTrajectoryService | Gait trajectory data |
| `gait-mode-changed` | GaitService | Gait mode change |
| `ai-state-changed` | AIStateService | AI state change | 
---

## Appendix A: Quick Examples 

HTTP — Playback Actions 

```bash
curl -X POST http://192.168.1.100:8088/api/v1/action/play -H "Content-Type: application/json" \
-d '{"action_name": "stand_default_wave", "torque": 1500}'
```

HTTP — Retrieving Battery Status 

```bash
curl http://192.168.1.100:8088/api/v1/battery/status
```

HTTP — Controlling Gait 
```bash
curl -X POST http://192.168.1.100:8088/api/v1/gait/move/forward -H "Content-Type: application/json" \
-d '{"speed": 0.2}'
```

WebSocket — Complete Interaction Process 
```javascript
const ws = new WebSocket('ws://192.168.1.100:8765?audience=script');

ws.onopen = () => {
  // Send request
  ws.send(JSON.stringify({
    type: 'request',
    request_id: 'req-001',
    request_type: 'BATTERY_GET_STATUS',
    data: {}
  }));
};

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);

  if (msg.type === 'response') {
    console.log(`Response [${msg.request_id}]:`, msg.data);
  }

  if (msg.type === 'event') {
    console.log(`Event [${msg.event_type}]:`, msg.data);
  }
};
```
