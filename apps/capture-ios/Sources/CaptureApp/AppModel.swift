#if os(iOS)
import CaptureKit
import Foundation
import SwiftUI
import UIKit

/// App-level state. Logic that can be tested without a device lives in CaptureKit.
@MainActor
final class AppModel: ObservableObject {
    enum Phase: Equatable {
        case needsPairing
        case ready
        case capturing
        case choosing(folder: URL)
        case reconstructing
        case submitting(done: Int, total: Int)
        case submitted(jobId: String, photos: Int)
        case failed(String)
    }

    @Published var phase: Phase
    /// A link waiting for the user to confirm its server. Nothing is stored until they do.
    @Published var pendingLink: PairingLink?
    var pairedHost: String? { pairing?.server.host }
    private let pairingStore = KeychainPairingStore()
    private var pairing: PairingLink?

    init() {
        pairing = pairingStore.load()
        phase = pairing == nil ? .needsPairing : .ready
    }

    /// Called for deep links and pasted text. Never pairs on its own: a crafted link must not be
    /// able to point the app (and the photos it uploads) at someone else's server.
    func receive(url: URL) {
        guard let link = PairingLink(url: url) else {
            phase = .failed("That is not a valid pairing link.")
            return
        }
        pendingLink = link
    }

    func confirmPending() {
        guard let link = pendingLink else { return }
        pendingLink = nil
        do {
            try pairingStore.save(link)
            pairing = link
            phase = .ready
        } catch {
            phase = .failed("Could not store the pairing: \(error.localizedDescription)")
        }
    }

    func rejectPending() { pendingLink = nil }

    func unpair() {
        pairingStore.clear()
        pairing = nil
        phase = .needsPairing
    }

    func captureFinished(folder: URL) { phase = .choosing(folder: folder) }
    func beginCapture() { phase = .capturing }
    func cancelCapture() { phase = .ready }

    static var device: CaptureManifest.Device {
        CaptureManifest.Device(
            model: UIDevice.current.model,
            systemVersion: UIDevice.current.systemVersion,
            appVersion: Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "0",
            hasLiDAR: ObjectCaptureAvailability.isSupported)
    }

    func submit(imagesDirectory: URL, name: String) async {
        guard let pairing else { phase = .needsPairing; return }
        let api = APIClient(transport: URLSessionTransport(baseURL: pairing.server, token: pairing.token))
        let store = FileUploadStore()
        let submission = Submission(api: api, uploader: ResumableUploader(api: api, store: store))
        phase = .submitting(done: 0, total: 1)
        do {
            let result = try await submission.submit(
                name: name, imagesDirectory: imagesDirectory, device: Self.device,
                onProgress: { done, total in
                    Task { @MainActor in self.phase = .submitting(done: done, total: total) }
                })
            phase = .submitted(jobId: result.jobId, photos: result.photoCount)
        } catch {
            phase = .failed("Upload failed: \(error). Your photos are kept, try again to resume.")
        }
    }

    /// Reconstructs on the phone and uploads the mesh. No Mac needed, but lower detail.
    func submitOnDevice(folder: URL, name: String) async {
        guard let pairing else { phase = .needsPairing; return }
        phase = .reconstructing
        let model = folder.appendingPathComponent("model.usdz")
        do {
            try await OnDeviceReconstruction.run(
                imagesDirectory: folder.appendingPathComponent("Images"), output: model)
            let api = APIClient(transport: URLSessionTransport(baseURL: pairing.server, token: pairing.token))
            let uploader = ResumableUploader(api: api, store: FileUploadStore())
            let job = try await api.createJob(name: name, sourceKind: "mesh")
            phase = .submitting(done: 0, total: 1)
            _ = try await uploader.upload(file: model, jobId: job.id, kind: "original")
            phase = .submitted(jobId: job.id, photos: 0)
        } catch {
            phase = .failed("On-device reconstruction failed: \(error)")
        }
    }
}
#endif
