import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const summaryPath = path.join(process.cwd(), 'public', 'data', 'summary.json');

    if (!fs.existsSync(summaryPath)) {
      return NextResponse.json(
        { error: 'Summary data not available' },
        { status: 404 }
      );
    }

    const summaryData = JSON.parse(fs.readFileSync(summaryPath, 'utf-8'));

    // Extract relevant update status information
    const updateStatus = {
      last_update: summaryData.generated_at,
      total_municipalities: summaryData.total_municipalities,
      successful_municipalities: summaryData.successful,
      failed_municipalities: summaryData.failed,
      carrier_stats: summaryData.carrier_stats || {},
      // Link to GitHub Actions for detailed logs
      github_actions_url: 'https://github.com/Ida-BirdsEye/pakketpunten/actions/workflows/update-data.yml'
    };

    return NextResponse.json(updateStatus);
  } catch (error) {
    console.error('Error reading update status:', error);
    return NextResponse.json(
      { error: 'Failed to read update status' },
      { status: 500 }
    );
  }
}
