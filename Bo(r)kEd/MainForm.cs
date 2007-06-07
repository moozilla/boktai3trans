/*
 * Created by SharpDevelop.
 * User: Spikeman
 * Date: 3/17/2007
 * 
 */

using System;
using System.Collections;
using System.Collections.Generic;
using System.Drawing;
using System.Windows.Forms;
using System.IO;
using System.Text;

namespace Borked
{
	
	public partial class MainForm : Form
	{
		
		#region Generated Stuff
		
		[STAThread]
		public static void Main(string[] args)
		{
			Application.EnableVisualStyles();
			Application.SetCompatibleTextRenderingDefault(false);
			Application.Run(new MainForm());
		}
		
		public MainForm()
		{
			//
			// The InitializeComponent() call is required for Windows Forms designer support.
			//
			InitializeComponent();
			
			//
			// TODO: Add constructor code after the InitializeComponent() call.
			//
		}
		
		#endregion		
		
		#region Defines
		
		Table tbl;
		bool tableLoaded = false;
		bool ROMLoaded = false;
		string ROMFile;
		
		#endregion
		
		void BLoadTableClick(object sender, EventArgs e)
		{
			if(openTable.ShowDialog() == DialogResult.OK) {
				tbl = new Table(openTable.FileName, Encoding.GetEncoding(932));
				tableLoaded = true;
				MessageBox.Show("Table loaded successfully.");
			}
		}
		
		void BLoadROMClick(object sender, EventArgs e)
		{
			if(openROM.ShowDialog() == DialogResult.OK) {
				ROMLoaded = true;
				ROMFile = openROM.FileName;
			}
		}
		
		void BDumpClick(object sender, EventArgs e)
		{
			if(tableLoaded & ROMLoaded) {
				if(saveDump.ShowDialog() == DialogResult.OK) {
					//FileStream ds = new FileStream(saveDump.FileName, FileMode.Create);
					StreamWriter tw = new StreamWriter(saveDump.FileName, false, tbl.Encoding, 0x61DB9);
					FileStream fs = new FileStream(ROMFile, FileMode.Open);
					BinaryReader br = new BinaryReader(fs);
					fs.Seek(0xD6B1F8, SeekOrigin.Begin);
					UInt32 offset = br.ReadUInt32();
					offset = (offset & 0x7FFFFFFF) + 0xD74DDC;
					fs.Seek(offset, SeekOrigin.Begin);
					ArrayList bytes = new ArrayList();
					byte[] str = br.ReadBytes(0x1000);
					tw.Write(tbl.fromTable(str)); //.Replace("[line]", "\r\n").Replace("[end]", "\r\n\r\n//==========\r\n\r\n"));
					tw.Flush();
					fs.Dispose();
					tw.Dispose();
					MessageBox.Show("Dump Successful!");
					}
			}
		}
	}
	
	public class Table : Dictionary<string,string>
	{
		public Encoding Encoding = Encoding.UTF8;
		
		public class LengthCompare : IComparer<string>
		{
			int IComparer<string>.Compare(string x, string y)
			{
				return y.Length - x.Length;		//sort backwards
			}
				
		}
		
		void ParseFile(string filename) {
			FileStream fs;
			try {
				fs = new FileStream(filename, FileMode.Open);
				StreamReader sr = new StreamReader(fs, this.Encoding);
				this.Clear();
				string line;
				ArrayList keyList = new ArrayList();
				ArrayList valList = new ArrayList();
				while((line = sr.ReadLine()) != null) {
					string[] parts = line.Split(new char[1] {'='}, 2);
					keyList.Add(parts[0]);
					valList.Add(parts[1]);
				}
				string[] keys = new string[keyList.Count]; string[] vals = new string[valList.Count];
				keyList.CopyTo(keys);
				valList.CopyTo(vals);
				Array.Sort(keys, vals, new LengthCompare());
				for(int i = 0; i < keys.Length; ++i) {
					this.Add(keys[i].ToLower(), vals[i]);
				}
			} catch {
				MessageBox.Show("Error accessing file or invalid table.");
			}
		}
		
		public void Sort(bool byKeys) {
			ArrayList keyList = new ArrayList();
			ArrayList valList = new ArrayList();
			keyList.AddRange(this.Keys);
			valList.AddRange(this.Values);
			string[] keys = new string[keyList.Count];
			string[] vals = new string[valList.Count];
			keyList.CopyTo(keys);
			valList.CopyTo(vals);
			if(byKeys) {
				Array.Sort(keys, vals, new LengthCompare());
			} else {
				Array.Sort(vals, keys, new LengthCompare());
			}
			this.Clear();
			for(int i = 0; i < keys.Length; ++i) {
				this.Add(keys[i], vals[i]);
			}
		}
		
		string bytesToString(byte[] bytes) {
			string str = "";
			foreach(byte b in bytes) {
				str += Convert.ToString(b, 16).PadLeft(2, '0');
			}
			return str;
		}
		
		public string fromTable(byte[] data) {
			string str = bytesToString(data);
			string ret = "";
			while(str != "") {
				foreach(KeyValuePair<string, string> kvp in this) {
					if(str.StartsWith(kvp.Key)) {
					   	ret += kvp.Value;
					   	str = str.Substring(kvp.Key.Length);
					   	break;
					}
				}
			}
			return ret;
		}
		
		public byte[] toTable(string data) {
			string str = data;
			ArrayList retList = new ArrayList();
			while(str != "") {
				foreach(KeyValuePair<string, string> kvp in this) {
					if(str.StartsWith(kvp.Value)) {
						retList.Add(Convert.ToByte(kvp.Key, 16));
					   	str = str.Substring(kvp.Value.Length);
					   	break;
					}
				}
			}
			byte[] ret = new byte[retList.Count];
			retList.CopyTo(ret);
			return ret;
		}
		
		public Table(string filename) {
			this.ParseFile(filename);
		}
		
		public Table(string filename, Encoding encode) {
			this.Encoding = encode;
			this.ParseFile(filename);
		}
		
	}
	
}
