const socket = io();
let localStream = null;
let peerConnection = null;
let isCallActive = false;

const servers = {
    iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' }
    ]
};

// UI Elements
const startButton = document.getElementById('startButton');
const endButton = document.getElementById('endButton');
const statusDiv = document.getElementById('status');

function updateStatus(message, type = 'info') {
    statusDiv.className = `alert alert-${type}`;
    statusDiv.textContent = message;
}

async function startCall() {
    try {
        startButton.disabled = true;
        updateStatus('Requesting camera and microphone access...', 'info');

        localStream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: true
        });

        document.getElementById('localVideo').srcObject = localStream;
        setupPeerConnection();
        
        endButton.disabled = false;
        isCallActive = true;
        updateStatus('Connected to local media. Waiting for peer...', 'success');
    } catch (error) {
        console.error('Error accessing media devices:', error);
        updateStatus('Failed to access camera/microphone. Please check permissions.', 'danger');
        startButton.disabled = false;
    }
}

function setupPeerConnection() {
    peerConnection = new RTCPeerConnection(servers);

    // Add local tracks to the connection
    localStream.getTracks().forEach(track => {
        peerConnection.addTrack(track, localStream);
    });

    // Handle remote stream
    peerConnection.ontrack = event => {
        document.getElementById('remoteVideo').srcObject = event.streams[0];
        updateStatus('Remote user connected!', 'success');
    };

    // Handle ICE candidates
    peerConnection.onicecandidate = event => {
        if (event.candidate) {
            socket.emit('ice-candidate', event.candidate);
        }
    };

    // Detect when the remote peer disconnects
    peerConnection.onconnectionstatechange = () => {
        if (peerConnection.connectionState === 'disconnected' || peerConnection.connectionState === 'failed' || peerConnection.connectionState === 'closed') {
            handleRemoteDisconnect();
        }
    };

    // Alternative method (older browsers)
    peerConnection.oniceconnectionstatechange = () => {
        if (peerConnection.iceConnectionState === 'disconnected' || peerConnection.iceConnectionState === 'failed') {
            handleRemoteDisconnect();
        }
    };

    // Create and send offer
    createAndSendOffer();
}

// Function to handle remote disconnection
function handleRemoteDisconnect() {
    document.getElementById('remoteVideo').srcObject = null;
    updateStatus('The remote user has disconnected.', 'danger');
}


function onDoctorConnected() {
    document.getElementById("doctorLoader").style.display = "none"; // Hide loader
    document.getElementById("remoteVideo").style.display = "block"; // Show video
}

// Example: Simulate doctor connecting after 3 seconds
setTimeout(onDoctorConnected, 3000);


async function createAndSendOffer() {
    try {
        const offer = await peerConnection.createOffer();
        await peerConnection.setLocalDescription(offer);
        console.log("Emitting offer:", offer);
        socket.emit('offer', offer);
    } catch (error) {
        console.error('Error creating offer:', error);
        updateStatus('Failed to create connection offer.', 'danger');
    }
}


function endCall() {
    if (localStream) {
        localStream.getTracks().forEach(track => track.stop());
        localStream = null;
    }

    if (peerConnection) {
        peerConnection.close();
        peerConnection = null;
    }

    document.getElementById('localVideo').srcObject = null;
    document.getElementById('remoteVideo').srcObject = null;

    startButton.disabled = false;
    endButton.disabled = true;
    isCallActive = false;

    updateStatus('Call ended.', 'info');
}

// Socket.IO event handlers
socket.on('connect', () => {
    updateStatus('Connected to signaling server.', 'info');
});

socket.on('offer', async offer => {
    console.log("Received offer:", offer);

    if (!peerConnection) {
        console.log("Initializing peer connection before setting remote description");
        await startCall();
    }

    try {
        await peerConnection.setRemoteDescription(new RTCSessionDescription(offer));
        console.log("Remote description set successfully");

        const answer = await peerConnection.createAnswer();
        await peerConnection.setLocalDescription(answer);
        console.log("Emitting answer:", answer);

        socket.emit('answer', answer);
    } catch (error) {
        console.error('Error handling offer:', error);
        updateStatus('Failed to handle incoming call.', 'danger');
    }
});


socket.on('answer', async answer => {
    try {
        await peerConnection.setRemoteDescription(new RTCSessionDescription(answer));
    } catch (error) {
        console.error('Error handling answer:', error);
        updateStatus('Failed to establish connection.', 'danger');
    }
});

socket.on('ice-candidate', async candidate => {
    console.log("Received ICE candidate:", candidate);
    try {
        if (peerConnection) {
            await peerConnection.addIceCandidate(new RTCIceCandidate(candidate));
            console.log("ICE candidate added successfully");
        }
    } catch (error) {
        console.error("Error adding ICE candidate:", error);
    }
});


socket.on('error', data => {
    updateStatus(data.message, 'danger');
});

// Handle page unload
window.onbeforeunload = () => {
    if (isCallActive) {
        endCall();
    }
};
