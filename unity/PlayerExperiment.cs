using System;
using System.Globalization;
using System.IO;
using UnityEngine;

// Компонент для пустого объекта Experiment в Unity (3D).
// Создаёт сцену и пишет события в Application.persistentDataPath.
public class PlayerExperiment : MonoBehaviour
{
    [Header("Идентификатор участника")]
    public int playerId = 1;
    [Header("Параметры сцены")]
    public float playerSpeed = 5f;
    public float movementLogInterval = 0.25f;
    private GameObject player;
    private GameObject target;
    private Camera sceneCamera;
    private float targetShownAt;
    private float lastMovementLoggedAt;
    private long sessionId;
    private string logPath;
    private int hits;
    private int misses;

    private void Start()
    {
        sessionId = DateTimeOffset.UtcNow.ToUnixTimeSeconds();
        logPath = Path.Combine(Application.persistentDataPath,
            "simulation_log_" + sessionId + ".csv");
        Directory.CreateDirectory(Application.persistentDataPath);
        File.WriteAllText(logPath,
            "player_id,session_id,timestamp,event_type,object_id,x_position,y_position,reaction_time,score\n");
        CreateScene();
        ShowTarget();
        Debug.Log("CSV-файл эксперимента: " + logPath);
    }

    private void CreateScene()
    {
        GameObject floor = GameObject.CreatePrimitive(PrimitiveType.Plane);
        floor.name = "Floor";
        floor.transform.position = new Vector3(0f, -0.1f, 0f);
        floor.transform.localScale = new Vector3(1.6f, 1f, 1.2f);

        player = GameObject.CreatePrimitive(PrimitiveType.Capsule);
        player.name = "Player";
        player.transform.position = new Vector3(-4f, 1f, 0f);
        player.transform.localScale = new Vector3(0.65f, 0.65f, 0.65f);

        target = GameObject.CreatePrimitive(PrimitiveType.Cube);
        target.name = "Target";
        target.transform.localScale = new Vector3(1f, 0.7f, 1f);

        sceneCamera = Camera.main;
        if (sceneCamera == null)
        {
            GameObject cameraObject = new GameObject("Main Camera");
            cameraObject.tag = "MainCamera";
            sceneCamera = cameraObject.AddComponent<Camera>();
        }
        sceneCamera.transform.position = new Vector3(0f, 17f, 0f);
        sceneCamera.transform.rotation = Quaternion.Euler(90f, 0f, 0f);
        sceneCamera.orthographic = true;
        sceneCamera.orthographicSize = 8.5f;
        sceneCamera.clearFlags = CameraClearFlags.Skybox;
    }

    private void Update()
    {
        UpdateMovement();
        HandleClick();
    }

    private void UpdateMovement()
    {
        float horizontal = Input.GetAxisRaw("Horizontal");
        float vertical = Input.GetAxisRaw("Vertical");
        Vector3 direction = new Vector3(horizontal, 0f, vertical).normalized;
        if (direction.sqrMagnitude < 0.001f)
            return;
        Vector3 next = player.transform.position + direction * playerSpeed * Time.deltaTime;
        next.x = Mathf.Clamp(next.x, -7f, 7f);
        next.z = Mathf.Clamp(next.z, -5f, 5f);
        player.transform.position = next;
        if (Time.realtimeSinceStartup - lastMovementLoggedAt >= movementLogInterval)
        {
            WriteEvent("move", 0, null, 0);
            lastMovementLoggedAt = Time.realtimeSinceStartup;
        }
    }

    private void HandleClick()
    {
        if (!Input.GetMouseButtonDown(0))
            return;
        Ray ray = sceneCamera.ScreenPointToRay(Input.mousePosition);
        RaycastHit hitInfo;
        bool targetHit = Physics.Raycast(ray, out hitInfo, 100f)
                         && hitInfo.collider.gameObject == target;
        if (targetHit)
        {
            float reactionSeconds = Time.realtimeSinceStartup - targetShownAt;
            WriteEvent("hit", 1, reactionSeconds, 1);
            hits++;
            ShowTarget();
        }
        else
        {
            WriteEvent("miss", 0, null, 0);
            misses++;
        }
    }

    private void ShowTarget()
    {
        target.transform.position = new Vector3(
            UnityEngine.Random.Range(-6f, 6f), 0.35f,
            UnityEngine.Random.Range(-4.5f, 4.5f)
        );
        targetShownAt = Time.realtimeSinceStartup;
    }

    private void WriteEvent(string eventType, int objectId, float? reaction, int score)
    {
        CultureInfo inv = CultureInfo.InvariantCulture;
        Vector3 position = player.transform.position;
        string reactionText = reaction.HasValue ? reaction.Value.ToString("F3", inv) : "";
        string row = string.Join(",", new string[] {
            playerId.ToString(inv),
            sessionId.ToString(inv),
            DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ss.fffZ", inv),
            eventType,
            objectId.ToString(inv),
            position.x.ToString("F3", inv),
            position.z.ToString("F3", inv),
            reactionText,
            score.ToString(inv)
        });
        File.AppendAllText(logPath, row + "\n");
    }

    private void OnGUI()
    {
        GUI.Label(new Rect(12, 12, 700, 28), "WASD — движение. ЛКМ по кубу — попадание.");
        GUI.Label(new Rect(12, 35, 700, 28),
            "Попадания: " + hits + "   Промахи: " + misses);
        GUI.Label(new Rect(12, 58, Screen.width - 20, 45), "CSV: " + logPath);
    }
}
