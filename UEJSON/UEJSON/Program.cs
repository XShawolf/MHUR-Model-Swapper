using UAssetAPI;
using UAssetAPI.UnrealTypes;

class Program
{
    static void Main(string[] args)
    {
        // Check arguments
        if (args.Length < 2)
        {
            Console.WriteLine("Usage: mycli -e|-i <file path>");
            return;
        }

        string mode = args[0];
        string path = args[1];

        switch (mode)
        {
            case "-e":
                ExportAsset(path);
                break;

            case "-i":
                ImportAsset(path);
                break;
        }
    }

    static void ExportAsset(string assetPath)
    {
        if (!File.Exists(assetPath))
        {
            Console.WriteLine($"File not found: {assetPath}");
            return;
        }

        try
        {
            UAsset asset = new UAsset(assetPath, EngineVersion.VER_UE4_27);
            string json = asset.SerializeJson();

            string jsonPath = Path.ChangeExtension(assetPath, ".json");
            File.WriteAllText(jsonPath, json);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error exporting asset: {ex.Message}");
        }
    }

    static void ImportAsset(string jsonPath)
    {
        if (!File.Exists(jsonPath))
        {
            Console.WriteLine($"File not found: {jsonPath}");
            return;
        }

        try
        {
            string jsonContent = File.ReadAllText(jsonPath);
            UAsset asset = UAsset.DeserializeJson(jsonContent);
            string outputPath = Path.ChangeExtension(jsonPath, ".uasset");
            asset.Write(outputPath);

        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error importing asset: {ex.Message}");
        }
    }
}
