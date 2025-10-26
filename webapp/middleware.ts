import { NextRequest, NextResponse } from 'next/server';

export function middleware(request: NextRequest) {
  // Check if request is for a .geojson file
  if (request.nextUrl.pathname.endsWith('.geojson')) {
    // Check if browser accepts gzip
    const acceptEncoding = request.headers.get('accept-encoding') || '';

    if (acceptEncoding.includes('gzip')) {
      // Redirect to .gz version
      const gzPath = request.nextUrl.pathname + '.gz';
      const url = request.nextUrl.clone();
      url.pathname = gzPath;

      // Rewrite to .gz file with proper headers
      const response = NextResponse.rewrite(url);
      response.headers.set('Content-Encoding', 'gzip');
      response.headers.set('Content-Type', 'application/geo+json');

      return response;
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    '/data/:path*.geojson',
    '/municipalities.json',
  ],
};
