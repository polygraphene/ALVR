#include "Settings.h"
#include "Logger.h"
#include "ipctools.h"
#include "resource.h"
#define PICOJSON_USE_INT64
#include <picojson.h>

extern uint64_t g_DriverTestMode;

Settings Settings::m_Instance;

Settings::Settings()
	: m_EnableOffsetPos(false)
	, m_loaded(false)
{
	m_OffsetPos[0] = 0.0f;
	m_OffsetPos[1] = 0.0f;
	m_OffsetPos[2] = 0.0f;
}


Settings::~Settings()
{
	if (m_DebugLog) {
		CloseLog();
	}
}

void Settings::Load()
{
	try {
		IPCFileMapping filemapping(APP_FILEMAPPING_NAME);
		if (!filemapping.Opened()) {
			return;
		}

		char *configBuf = (char *)filemapping.Map();
		int32_t size = *(int32_t *)configBuf;

		std::string json(configBuf + sizeof(int32_t), size);

		picojson::value v;
		std::string err = picojson::parse(v, json);
		if (!err.empty()) {
			FatalLog(L"Error on parsing json: %hs", err.c_str());
			return;
		}

		m_sSerialNumber = v.get(k_pch_Settings_SerialNumber_String).get<std::string>();
		m_sModelNumber = v.get(k_pch_Settings_ModelNumber_String).get<std::string>();

		m_renderWidth = (int32_t)v.get(k_pch_Settings_RenderWidth_Int32).get<int64_t>();
		m_renderHeight = (int32_t)v.get(k_pch_Settings_RenderHeight_Int32).get<int64_t>();

		picojson::array& eyeFov = v.get(k_pch_Settings_EyeFov).get<picojson::array>();
		for (int eye = 0; eye < 2; eye++) {
			m_eyeFov[eye].left = static_cast<float>(eyeFov[eye * 4 + 0].get<double>());
			m_eyeFov[eye].right = static_cast<float>(eyeFov[eye * 4 + 1].get<double>());
			m_eyeFov[eye].top = static_cast<float>(eyeFov[eye * 4 + 2].get<double>());
			m_eyeFov[eye].bottom = static_cast<float>(eyeFov[eye * 4 + 3].get<double>());
		}

		m_enableSound = v.get(k_pch_Settings_EnableSound_Bool).get<bool>();
		m_soundDevice = v.get(k_pch_Settings_SoundDevice_String).get<std::string>();

		m_flSecondsFromVsyncToPhotons = (float)v.get(k_pch_Settings_SecondsFromVsyncToPhotons_Float).get<double>();

		m_flIPD = (float)v.get(k_pch_Settings_IPD_Float).get<double>();

		m_clientRecvBufferSize = (uint32_t)v.get(k_pch_Settings_ClientRecvBufferSize_Int32).get<int64_t>();
		m_frameQueueSize = (uint32_t)v.get(k_pch_Settings_FrameQueueSize_Int32).get<int64_t>();

		m_force60HZ = v.get(k_pch_Settings_Force60HZ_Bool).get<bool>();

		m_nAdapterIndex = (int32_t)v.get(k_pch_Settings_AdapterIndex_Int32).get<int64_t>();

		m_codec = (int32_t)v.get(k_pch_Settings_Codec_Int32).get<int64_t>();
		m_refreshRate = (int)v.get(k_pch_Settings_RefreshRate_Int32).get<int64_t>();
		m_encodeBitrateInMBits = (int)v.get(k_pch_Settings_EncodeBitrateInMBits_Int32).get<int64_t>();

		m_DebugOutputDir = v.get(k_pch_Settings_DebugOutputDir).get<std::string>();

		// Listener Parameters
		m_Host = v.get(k_pch_Settings_ListenHost_String).get<std::string>();
		m_Port = (int)v.get(k_pch_Settings_ListenPort_Int32).get<int64_t>();

		m_SendingTimeslotUs = (uint64_t)v.get(k_pch_Settings_SendingTimeslotUs_Int32).get<int64_t>();
		m_LimitTimeslotPackets = (uint64_t)v.get(k_pch_Settings_LimitTimeslotPackets_Int32).get<int64_t>();

		m_ControlHost = v.get(k_pch_Settings_ControlListenHost_String).get<std::string>();
		m_ControlPort = (int)v.get(k_pch_Settings_ControlListenPort_Int32).get<int64_t>();

		m_AutoConnectHost = v.get(k_pch_Settings_AutoConnectHost_String).get<std::string>();
		m_AutoConnectPort = (int)v.get(k_pch_Settings_AutoConnectPort_Int32).get<int64_t>();

		m_DebugLog = v.get(k_pch_Settings_DebugLog_Bool).get<bool>();
		m_DebugFrameIndex = v.get(k_pch_Settings_DebugFrameIndex_Bool).get<bool>();
		m_DebugFrameOutput = v.get(k_pch_Settings_DebugFrameOutput_Bool).get<bool>();
		m_DebugCaptureOutput = v.get(k_pch_Settings_DebugCaptureOutput_Bool).get<bool>();
		m_UseKeyedMutex = v.get(k_pch_Settings_UseKeyedMutex_Bool).get<bool>();

		m_controllerTrackingSystemName = v.get(k_pch_Settings_ControllerTrackingSystemName_String).get<std::string>();
		m_controllerManufacturerName = v.get(k_pch_Settings_ControllerManufacturerName_String).get<std::string>();
		m_controllerModelNumber = v.get(k_pch_Settings_ControllerModelNumber_String).get<std::string>();
		m_controllerRenderModelNameLeft = v.get(k_pch_Settings_ControllerRenderModelNameLeft_String).get<std::string>();
		m_controllerRenderModelNameRight = v.get(k_pch_Settings_ControllerRenderModelNameRight_String).get<std::string>();
		m_controllerSerialNumber = v.get(k_pch_Settings_ControllerSerialNumber_String).get<std::string>();
		m_controllerType = v.get(k_pch_Settings_ControllerType_String).get<std::string>();
		m_controllerLegacyInputProfile = v.get(k_pch_Settings_ControllerLegacyInputProfile_String).get<std::string>();
		m_controllerInputProfilePath = v.get(k_pch_Settings_ControllerInputProfilePath_String).get<std::string>();

		m_enableController = v.get(k_pch_Settings_EnableController_Bool).get<bool>();
		m_controllerTriggerMode = (int32_t)v.get(k_pch_Settings_ControllerTriggerMode_Int32).get<int64_t>();
		m_controllerTrackpadClickMode = (int32_t)v.get(k_pch_Settings_ControllerTrackpadClickMode_Int32).get<int64_t>();
		m_controllerTrackpadTouchMode = (int32_t)v.get(k_pch_Settings_ControllerTrackpadTouchMode_Int32).get<int64_t>();
		m_controllerBackMode = (int32_t)v.get(k_pch_Settings_ControllerBackMode_Int32).get<int64_t>();
		m_controllerRecenterButton = (int32_t)v.get(k_pch_Settings_ControllerRecenterButton_Int32).get<int64_t>();

		m_useTrackingReference = v.get(k_pch_Settings_UseTrackingReference_Bool).get<bool>();

		m_EnableOffsetPos = v.get(k_pch_Settings_EnableOffsetPos_Bool).get<bool>();
		m_OffsetPos[0] = (float)v.get(k_pch_Settings_OffsetPosX_Float).get<double>();
		m_OffsetPos[1] = (float)v.get(k_pch_Settings_OffsetPosY_Float).get<double>();
		m_OffsetPos[2] = (float)v.get(k_pch_Settings_OffsetPosZ_Float).get<double>();

		m_trackingFrameOffset = (int32_t)v.get(k_pch_Settings_TrackingFrameOffset_Int32).get<int64_t>();

		if (m_DebugLog) {
			OpenLog((m_DebugOutputDir + "\\" + LOG_FILE).c_str());
		}

		Log(L"Serial Number: %hs", m_sSerialNumber.c_str());
		Log(L"Model Number: %hs", m_sModelNumber.c_str());
		Log(L"Render Target: %d %d", m_renderWidth, m_renderHeight);
		Log(L"Seconds from Vsync to Photons: %f", m_flSecondsFromVsyncToPhotons);
		Log(L"Refresh Rate: %d", m_refreshRate);
		Log(L"IPD: %f", m_flIPD);

		Log(L"debugOptions: Log:%d FrameIndex:%d FrameOutput:%d CaptureOutput:%d UseKeyedMutex:%d"
			, m_DebugLog, m_DebugFrameIndex, m_DebugFrameOutput, m_DebugCaptureOutput, m_UseKeyedMutex);
		Log(L"EncoderOptions: %hs", m_EncoderOptions.c_str());

		m_loaded = true;
	}
	catch (std::exception &e) {
		FatalLog(L"Exception on parsing json: %hs", e.what());
	}
}
