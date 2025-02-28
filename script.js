import { MuseClient } from 'muse-js';
import fs from 'fs';

const logStream = fs.createWriteStream('eeg_data.csv', { flags: 'a' });

async function recordEEG() {
    const client = new MuseClient();
    
    await client.connect();
    await client.start();

    client.eegReadings.subscribe(reading => {
        const timestamp = new Date().toISOString();
        const dataString = `${timestamp},${reading.samples.join(',')}\n`;
        logStream.write(dataString);
    });

    // Add other data streams as needed:
    client.accelerometerData.subscribe(acc => {
        // Handle accelerometer data
    });
}

recordEEG().catch(console.error);
