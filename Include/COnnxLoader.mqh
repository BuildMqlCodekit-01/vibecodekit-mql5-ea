//+------------------------------------------------------------------+
//| COnnxLoader.mqh — ONNX inference wrapper for MQL5 (build 4620+)  |
//|                                                                   |
//| Loads a resource-embedded or file-backed ONNX model and exposes  |
//| a minimal Run(inputs, outputs) API. Compatible with MetaTrader 5 |
//| build 4620+ (October 2024) where OnnxCreate / OnnxRun were added.|
//|                                                                   |
//| Usage:                                                            |
//|   COnnxLoader onnx;                                               |
//|   if(!onnx.InitFromResource("model.onnx")) return INIT_FAILED;    |
//|   float in[10], out[1];                                           |
//|   if(onnx.Run(in, ArraySize(in), out, ArraySize(out)))            |
//|     ...use out[0]...                                              |
//+------------------------------------------------------------------+
#ifndef __COnnxLoader_MQH__
#define __COnnxLoader_MQH__

class COnnxLoader
  {
private:
   long              m_handle;
   string            m_path;
public:
                     COnnxLoader(void):m_handle(INVALID_HANDLE),m_path("") {}
                    ~COnnxLoader(void) { Release(); }

   bool              InitFromResource(const string resource_name)
     {
      // ONNX runtime needs the model bytes — for a #resource embed we pass
      // the resource name; runtime will read it via the platform.
      m_path = resource_name;
      m_handle = OnnxCreate(resource_name, 0);
      if(m_handle == INVALID_HANDLE)
        {
         Print("[OnnxLoader] OnnxCreate failed for ", resource_name,
               " err=", GetLastError());
         return false;
        }
      Print("[OnnxLoader] loaded ", resource_name);
      return true;
     }

   bool              InitFromFile(const string file_path)
     {
      // Load the file into a byte buffer first, then feed it to
      // OnnxCreateFromBuffer(const uchar &buffer[], ulong flags) — the
      // MQL5 runtime signature is (buffer, flags), NOT (path, ..., ...).
      m_path = file_path;
      uchar buf[];
      const int fh = FileOpen(file_path, FILE_BIN|FILE_READ|FILE_COMMON);
      if(fh == INVALID_HANDLE)
        {
         Print("[OnnxLoader] FileOpen failed for ", file_path,
               " err=", GetLastError());
         return false;
        }
      const ulong size = FileSize(fh);
      ArrayResize(buf, (int)size);
      FileReadArray(fh, buf, 0, (int)size);
      FileClose(fh);
      m_handle = OnnxCreateFromBuffer(buf, 0);
      if(m_handle == INVALID_HANDLE)
        {
         Print("[OnnxLoader] OnnxCreateFromBuffer failed for ", file_path,
               " err=", GetLastError());
         return false;
        }
      return true;
     }

   bool              Run(const float &inputs[], const int n_in,
                         float &outputs[], const int n_out)
     {
      if(m_handle == INVALID_HANDLE) return false;
      const ulong t0 = GetMicrosecondCount();
      const bool ok = OnnxRun(m_handle, ONNX_DEFAULT, inputs, outputs);
      const ulong dt = GetMicrosecondCount() - t0;
      if(!ok)
         Print("[OnnxLoader] OnnxRun failed err=", GetLastError(),
               " latency_us=", dt);
      return ok;
     }

   void              Release(void)
     {
      if(m_handle != INVALID_HANDLE)
        {
         OnnxRelease(m_handle);
         m_handle = INVALID_HANDLE;
        }
     }

   long              Handle(void) const { return m_handle; }
   string            Path(void)   const { return m_path; }
  };

#endif // __COnnxLoader_MQH__
