#pragma once
#include <openvr_driver.h>
#include "Utils.h"
#include "Logger.h"
#include "packet_types.h"
#include "FreePIE.h"
#include "RemoteController.h"
#include "SimpleMath.h"
using namespace DirectX::SimpleMath;

class RecenterManager
{
public:
	RecenterManager()
		: m_hasValidTrackingInfo(false)
		, m_recentering(false)
		, m_recenterStartTimestamp(0)
		, m_centerPitch(0.0)
		, m_rotationDiffLastInitialized(0)
		, m_freePIE(std::make_shared<FreePIE>())
		, m_controllerDetected(false)
	{
	}

	bool HasValidTrackingInfo() {
		return m_hasValidTrackingInfo;
	}

	bool IsRecentering() {
		return m_recentering;
	}

	void BeginRecenter() {
		m_recenterStartTimestamp = GetTimestampUs();
		m_recentering = true;
	}

	void EndRecenter() {
		m_recentering = false;
	}

	void OnPoseUpdated(const TrackingInfo &info) {
		m_hasValidTrackingInfo = true;
		if (m_recentering) {
			if (GetTimestampUs() - m_recenterStartTimestamp > RECENTER_DURATION) {
				m_centerPitch = PitchFromQuaternion(info.HeadPose_Pose_Orientation);

				Log(L"Do recentered: Cur=(%f,%f,%f,%f) pitch=%f"
					, info.HeadPose_Pose_Orientation.x
					, info.HeadPose_Pose_Orientation.y
					, info.HeadPose_Pose_Orientation.z
					, info.HeadPose_Pose_Orientation.w
					, m_centerPitch
				);

				m_recentering = false;
			}
		}

		m_fixedOrientationHMD = MultiplyPitchQuaternion(
			-m_centerPitch
			, info.HeadPose_Pose_Orientation.x
			, info.HeadPose_Pose_Orientation.y
			, info.HeadPose_Pose_Orientation.z
			, info.HeadPose_Pose_Orientation.w);

		m_fixedPositionHMD = RotateVectorQuaternion(info.HeadPose_Pose_Position, m_centerPitch);

		m_fixedOrientationController = MultiplyPitchQuaternion(
			-m_centerPitch
			, info.controller_Pose_Orientation.x
			, info.controller_Pose_Orientation.y
			, info.controller_Pose_Orientation.z
			, info.controller_Pose_Orientation.w);

		m_fixedPositionController = RotateVectorQuaternion(info.controller_Pose_Position, m_centerPitch);

		if (info.flags & TrackingInfo::FLAG_OTHER_TRACKING_SOURCE) {
			UpdateOtherTrackingSource(info);
		}
		/*Log(L"GetRecenteredHMD: Old=(%f,%f,%f,%f) New=(%f,%f,%f,%f) pitch=%f-%f"
			, info.HeadPose_Pose_Orientation.x, info.HeadPose_Pose_Orientation.y
			, info.HeadPose_Pose_Orientation.z, info.HeadPose_Pose_Orientation.w
			, m_fixedOrientationHMD.x, m_fixedOrientationHMD.y
			, m_fixedOrientationHMD.z, m_fixedOrientationHMD.w
			, m_centerPitch
			, PitchFromQuaternion(
				m_fixedOrientationHMD.x
				, m_fixedOrientationHMD.y
				, m_fixedOrientationHMD.z
				, m_fixedOrientationHMD.w));
		Log(L"GetRecenteredController: Old=(%f,%f,%f,%f) New=(%f,%f,%f,%f) pitch=%f-%f"
			, info.controller_Pose_Orientation.x, info.controller_Pose_Orientation.y
			, info.controller_Pose_Orientation.z, info.controller_Pose_Orientation.w
			, m_fixedOrientationController.x, m_fixedOrientationController.y
			, m_fixedOrientationController.z, m_fixedOrientationController.w
			, m_centerPitch
			, PitchFromQuaternion(
				m_fixedOrientationController.x
				, m_fixedOrientationController.y
				, m_fixedOrientationController.z
				, m_fixedOrientationController.w));*/

		m_freePIE->UpdateTrackingInfoByFreePIE(info, m_fixedOrientationHMD, m_fixedOrientationController, m_fixedPositionHMD, m_fixedPositionController);

		auto data = m_freePIE->GetData();

		if (data.flags & FreePIE::ALVR_FREEPIE_FLAG_OVERRIDE_HEAD_ORIENTATION) {
			m_fixedOrientationHMD = EulerAngleToQuaternion(data.head_orientation);
		}
		if (data.flags & FreePIE::ALVR_FREEPIE_FLAG_OVERRIDE_CONTROLLER_ORIENTATION0) {
			m_fixedOrientationController = EulerAngleToQuaternion(data.controller_orientation[0]);
		}
		if (data.flags & FreePIE::ALVR_FREEPIE_FLAG_OVERRIDE_HEAD_POSITION) {
			m_fixedPositionHMD.x = (float) data.head_position[0];
			m_fixedPositionHMD.y = (float) data.head_position[1];
			m_fixedPositionHMD.z = (float) data.head_position[2];
		}
		if (data.flags & FreePIE::ALVR_FREEPIE_FLAG_OVERRIDE_CONTROLLER_POSITION0) {
			m_fixedPositionController.x = (float) data.controller_position[0][0];
			m_fixedPositionController.y = (float) data.controller_position[0][1];
			m_fixedPositionController.z = (float) data.controller_position[0][2];
		}

		if (Settings::Instance().m_EnableOffsetPos) {
			m_fixedPositionHMD.x += Settings::Instance().m_OffsetPos[0];
			m_fixedPositionHMD.y += Settings::Instance().m_OffsetPos[1];
			m_fixedPositionHMD.z += Settings::Instance().m_OffsetPos[2];
		}
		if (Settings::Instance().m_EnableOffsetPos) {
			m_fixedPositionController.x += Settings::Instance().m_OffsetPos[0];
			m_fixedPositionController.y += Settings::Instance().m_OffsetPos[1];
			m_fixedPositionController.z += Settings::Instance().m_OffsetPos[2];
		}

		UpdateControllerState(info);
	}

	vr::HmdQuaternion_t GetRecenteredHMD() {
		return m_fixedOrientationHMD;
	}

	TrackingVector3 GetRecenteredPositionHMD() {
		return m_fixedPositionHMD;
	}

	std::string GetFreePIEMessage() {
		return m_freePIE->GetData().message;
	}

private:
	void UpdateOtherTrackingSource(const TrackingInfo &info) {
		if (m_rotationDiffLastInitialized == 0) {
			m_basePosition = info.Other_Tracking_Source_Position;
			m_rotationDiff = 0.0;
			m_rotatedBasePosition = m_basePosition;
		}
		TrackingVector3 transformed;
		double theta = m_rotationDiff + m_centerPitch;
		transformed.x = (float) ((info.Other_Tracking_Source_Position.x - m_basePosition.x) * cos(theta) - (info.Other_Tracking_Source_Position.z - m_basePosition.z) * sin(theta));
		transformed.y = info.Other_Tracking_Source_Position.y;
		transformed.z = (float)((info.Other_Tracking_Source_Position.x - m_basePosition.x) * sin(theta) + (info.Other_Tracking_Source_Position.z - m_basePosition.z) * cos(theta));

		transformed.x += m_rotatedBasePosition.x;
		transformed.z += m_rotatedBasePosition.z;

		if (GetTimestampUs() - m_rotationDiffLastInitialized > 2 * 1000 * 1000) {
			double p1 = PitchFromQuaternion(info.Other_Tracking_Source_Orientation);
			double pitch_tracking = PitchFromQuaternion(info.HeadPose_Pose_Orientation);
			double diff = p1 - pitch_tracking;
			if (diff < 0) {
				diff += M_PI * 2;
			}

			m_rotationDiffLastInitialized = GetTimestampUs();
			m_rotationDiff = diff;
			m_basePosition = info.Other_Tracking_Source_Position;

			m_rotatedBasePosition = transformed;
		}

		m_fixedPositionHMD.x += transformed.x;
		m_fixedPositionHMD.y += transformed.y;
		m_fixedPositionHMD.z += transformed.z;

		m_fixedPositionController.x += transformed.x;
		m_fixedPositionController.y += transformed.y;
		m_fixedPositionController.z += transformed.z;

		Log(L"OtherTrackingSource (diff:%f) (%f,%f,%f) (%f,%f,%f)",
			info.Other_Tracking_Source_Position.x,
			info.Other_Tracking_Source_Position.y,
			info.Other_Tracking_Source_Position.z,
			transformed.x, transformed.y, transformed.z);
	}

	TrackingVector3 CalculateVelocity(const TrackingVector3& newPosition, const TrackingVector3& oldPosition, float deltaTime)
	{
		return RotateVectorQuaternion_scale(1.0f / deltaTime, RotateVectorQuaternion_sub(newPosition, oldPosition));
	}

	const float LERP_VELOCITY_PER_FRAME = 0.1f;

	const float LERP_ANGLE_PER_FRAME = 0.1f;

	void UpdateControllerState(const TrackingInfo& info) {
		if (!Settings::Instance().m_enableController) {
			return;
		}
		auto data = m_freePIE->GetData();
		bool enableControllerButton = data.flags & FreePIE::ALVR_FREEPIE_FLAG_OVERRIDE_BUTTONS;
		m_controllerDetected = data.controllers;

		// Add controller as specified.
		for (int i = 0; i < m_controllerDetected; i++) {
			if (m_remoteController[i]) {
				// Already enabled.
				continue;
			}
			// false: right hand, true: left hand
			bool handed = (info.flags & TrackingInfo::FLAG_CONTROLLER_LEFTHAND) != 0;
			if (i == 1) {
				handed = !handed;
			}
			m_remoteController[i] = std::make_shared<RemoteControllerServerDriver>(handed, i);

			bool ret = vr::VRServerDriverHost()->TrackedDeviceAdded(
				m_remoteController[i]->GetSerialNumber().c_str(),
				vr::TrackedDeviceClass_Controller,
				m_remoteController[i].get());
			Log(L"TrackedDeviceAdded vr::TrackedDeviceClass_Controller index=%d Ret=%d SerialNumber=%hs"
				, i, ret, m_remoteController[i]->GetSerialNumber().c_str());
		}

		float deltaTime = float(clock() - mlastUpdateTime) / CLOCKS_PER_SEC;

		if (deltaTime > 0.0f) {

			mlastUpdateTime = clock();

			if (m_remoteController[0]) {

				TrackingVector3 newVelocity = CalculateVelocity(m_fixedPositionController, m_LastControllerPosition[0], deltaTime);

				//newVelocity.x = clamp(newVelocity.x, -5.0f, 5.0f);
				//newVelocity.y = clamp(newVelocity.y, -5.0f, 5.0f);
				//newVelocity.z = clamp(newVelocity.z, -5.0f, 5.0f);

				linearVelocity[0] = TrackingVector3::lerp(linearVelocity[0], newVelocity, LERP_VELOCITY_PER_FRAME);//lerp(linearVelocity[0].x, newVelocity.x, 60 * deltaTime);
				
				double eulerAngles[3];

				Quaternion controllerRotation = Quaternion(m_fixedOrientationController.x, m_fixedOrientationController.y, m_fixedOrientationController.z, m_fixedOrientationController.w);
				lastRotation.Inverse(lastRotation);
				Quaternion deltaRotation = lastRotation * controllerRotation;

				lastRotation = controllerRotation;

				vr::HmdQuaternion_t deltaRotationQ;
				deltaRotationQ.x = deltaRotation.x;
				deltaRotationQ.y = deltaRotation.y;
				deltaRotationQ.z = deltaRotation.z;
				deltaRotationQ.w = deltaRotation.w;

				double deltaRotationEuler[3];

				QuaternionToEulerAngle(deltaRotationQ, deltaRotationEuler);

				TrackingVector3 newAngularVelocity = TrackingVector3(deltaRotationEuler[0] / deltaTime, deltaRotationEuler[1] / deltaTime, deltaRotationEuler[2] / deltaTime);

				newAngularVelocity.x = clamp(newAngularVelocity.x, -1.0f, 1.0f);
				newAngularVelocity.y = clamp(newAngularVelocity.y, -1.0f, 1.0f);
				newAngularVelocity.z = clamp(newAngularVelocity.z, -1.0f, 1.0f);

				QuaternionToEulerAngle(m_fixedOrientationController, eulerAngles);

				//TrackingVector3 currentRotation = TrackingVector3(eulerAngles[0], eulerAngles[1], eulerAngles[2]);

				//TrackingVector3 newAngularVelocity = (currentRotation - lastRotationEuler[0]) / deltaTime;

				angularVelocity[0] = TrackingVector3::lerp(angularVelocity[0], newAngularVelocity, LERP_ANGLE_PER_FRAME);

				double euler[3] = { lastRotationEuler[0].x, lastRotationEuler[0].y, lastRotationEuler[0].z };

				bool recenterRequested = m_remoteController[0]->ReportControllerState(info, EulerAngleToQuaternion(euler), m_LastControllerPosition[0], linearVelocity[0], angularVelocity[0], enableControllerButton, data);

				m_LastControllerPosition[0] = m_fixedPositionController;

				lastRotationEuler[0] = TrackingVector3(eulerAngles[0], eulerAngles[1], eulerAngles[2]);

				if (recenterRequested) {
					BeginRecenter();
				}
			}
			if (m_remoteController[1]) {

				TrackingVector3 positionController1;
				positionController1.x = (float)data.controller_position[1][0];
				positionController1.y = (float)data.controller_position[1][1];
				positionController1.z = (float)data.controller_position[1][2];

				double eulerAngles[3];
				eulerAngles[0] = data.controller_orientation[1][0];
				eulerAngles[1] = data.controller_orientation[1][1];
				eulerAngles[2] = data.controller_orientation[1][2];

				TrackingVector3 currentRotation = TrackingVector3(eulerAngles[0], eulerAngles[1], eulerAngles[2]);

				TrackingVector3 newAngularVelocity = (currentRotation - lastRotationEuler[1]) / deltaTime;

				angularVelocity[1] = TrackingVector3::lerp(angularVelocity[1], newAngularVelocity, LERP_ANGLE_PER_FRAME);

				vr::HmdQuaternion_t controllerOrientation = EulerAngleToQuaternion(eulerAngles);

				TrackingVector3 newVelocity = CalculateVelocity(positionController1, m_LastControllerPosition[1], deltaTime);

				//newVelocity.x = clamp(newVelocity.x, -5.0f, 5.0f);
				//newVelocity.y = clamp(newVelocity.y, -5.0f, 5.0f);
				//newVelocity.z = clamp(newVelocity.z, -5.0f, 5.0f);

				linearVelocity[1] = TrackingVector3::lerp(linearVelocity[1], newVelocity, LERP_VELOCITY_PER_FRAME);

				double euler[3] = { eulerAngles[0], eulerAngles[1], eulerAngles[2] };

				bool recenterRequested = m_remoteController[1]->ReportControllerState(info, EulerAngleToQuaternion(euler), positionController1, linearVelocity[1], angularVelocity[1], enableControllerButton, data);
				if (recenterRequested) {
					BeginRecenter();
				}

				m_LastControllerPosition[1] = positionController1;

				lastRotationEuler[1] = TrackingVector3(eulerAngles[0], eulerAngles[1], eulerAngles[2]);
			}
		}
	}

	int m_controllerDetected;
	std::shared_ptr<RemoteControllerServerDriver> m_remoteController[2];

	std::shared_ptr<FreePIE> m_freePIE;

	bool m_hasValidTrackingInfo;
	bool m_recentering;
	uint64_t m_recenterStartTimestamp;
	double m_centerPitch;
	vr::HmdQuaternion_t m_fixedOrientationHMD;
	TrackingVector3 m_fixedPositionHMD;
	vr::HmdQuaternion_t m_fixedOrientationController;
	TrackingVector3 m_fixedPositionController;

	TrackingVector3 m_basePosition;
	TrackingVector3 m_rotatedBasePosition;
	double m_rotationDiff;
	uint64_t m_rotationDiffLastInitialized;

	static const int RECENTER_DURATION = 400 * 1000;

	TrackingVector3 lastRotationEuler[2];
	Quaternion lastRotation;
	TrackingVector3 m_LastControllerPosition[2];
	TrackingVector3 linearVelocity[2];
	TrackingVector3 angularVelocity[2];
	clock_t mlastUpdateTime = 0;
};
