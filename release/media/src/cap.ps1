# Screen recorder that works here: GDI CopyFromScreen frames (+ cursor) piped as raw BGRA into ffmpeg (NVENC).
# ffmpeg's own grabbers (gfxcapture, ddagrab, gdigrab) all returned a frozen desktop from this shell.
param([string]$Out, [int]$Seconds = 30, [int]$Fps = 24, [int]$W = 1920, [int]$H = 1200)
Add-Type -AssemblyName System.Drawing
Add-Type -ReferencedAssemblies System.Drawing @'
using System; using System.Diagnostics; using System.Drawing; using System.Drawing.Imaging; using System.IO; using System.Runtime.InteropServices; using System.Threading;
public class Cap {
  [StructLayout(LayoutKind.Sequential)] public struct PT { public int X, Y; }
  [StructLayout(LayoutKind.Sequential)] public struct CI { public int cbSize, flags; public IntPtr hCursor; public PT pt; }
  [DllImport("user32.dll")] static extern bool GetCursorInfo(ref CI ci);
  [DllImport("user32.dll")] static extern bool DrawIconEx(IntPtr hdc, int x, int y, IntPtr hIcon, int w, int h, int step, IntPtr brush, int flags);
  [DllImport("user32.dll")] static extern bool GetIconInfo(IntPtr hIcon, out II ii);
  [DllImport("gdi32.dll")] static extern bool DeleteObject(IntPtr h);
  [StructLayout(LayoutKind.Sequential)] public struct II { public bool fIcon; public int xHotspot, yHotspot; public IntPtr hbmMask, hbmColor; }
  public static string Run(string ffmpeg, string outPath, int seconds, int fps, int w, int h) {
    var psi = new ProcessStartInfo(ffmpeg, string.Format("-hide_banner -loglevel error -y -f rawvideo -pixel_format bgra -video_size {0}x{1} -framerate {2} -i pipe:0 -c:v h264_nvenc -preset p5 -rc vbr -cq 19 -b:v 0 -pix_fmt yuv420p \"{3}\"", w, h, fps, outPath));
    psi.UseShellExecute = false; psi.RedirectStandardInput = true; psi.CreateNoWindow = true;
    var p = Process.Start(psi); var stdin = p.StandardInput.BaseStream;
    var bmp = new Bitmap(w, h, PixelFormat.Format32bppArgb); var g = Graphics.FromImage(bmp);
    var buf = new byte[w * h * 4]; var sw = Stopwatch.StartNew(); long frames = 0, total = (long)seconds * fps; double period = 1000.0 / fps; long late = 0;
    while (frames < total) {
      double due = frames * period; double now = sw.Elapsed.TotalMilliseconds;
      if (now < due) Thread.Sleep((int)(due - now)); else if (now - due > period) late++;
      g.CopyFromScreen(0, 0, 0, 0, bmp.Size, CopyPixelOperation.SourceCopy);
      var ci = new CI(); ci.cbSize = Marshal.SizeOf(typeof(CI));
      if (GetCursorInfo(ref ci) && ci.flags == 1) { II ii; int hx = 0, hy = 0; if (GetIconInfo(ci.hCursor, out ii)) { hx = ii.xHotspot; hy = ii.yHotspot; if (ii.hbmMask != IntPtr.Zero) DeleteObject(ii.hbmMask); if (ii.hbmColor != IntPtr.Zero) DeleteObject(ii.hbmColor); }
        IntPtr hdc = g.GetHdc(); DrawIconEx(hdc, ci.pt.X - hx, ci.pt.Y - hy, ci.hCursor, 0, 0, 0, IntPtr.Zero, 3); g.ReleaseHdc(hdc); }
      var d = bmp.LockBits(new Rectangle(0, 0, w, h), ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
      Marshal.Copy(d.Scan0, buf, 0, buf.Length); bmp.UnlockBits(d);
      stdin.Write(buf, 0, buf.Length); frames++;
    }
    stdin.Close(); p.WaitForExit();
    return string.Format("frames={0} late={1} elapsed={2:F1}s exit={3}", frames, late, sw.Elapsed.TotalSeconds, p.ExitCode);
  }
}
'@
[Cap]::Run("$env:LOCALAPPDATA\universal-modder\ffmpeg\bin\ffmpeg.exe", $Out, $Seconds, $Fps, $W, $H)
