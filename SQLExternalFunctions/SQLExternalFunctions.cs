using System;
using System.Data.SqlTypes;
using System.Net;
using RestSharp;

public static class SQLExternalFunctions
{
    /// <summary>
    /// Execute python script via API
    /// </summary>
    /// <param name="scriptName">must end with .py</param>
    /// <param name="waitFlag">true - wait for successful execution. false - add to queue</param>
    /// <param name="parameters"></param>
    /// <exception cref="Exception">Throws exception in case of any failure, it's desirable behaviour</exception>
    public static void ExecutePython(SqlString scriptName, SqlBoolean waitFlag, SqlString parameters)
    {
        // 1 Config
        string token = "TOKEN123"; // TODO: Implement tokens on production
        Uri baseUrl = new Uri("https://localhost:8090");  // TODO: Replace with production URL
        ServicePointManager.Expect100Continue = true;
        ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12;
        ServicePointManager.ServerCertificateValidationCallback = (senderX, certificate, chain, sslPolicyErrors) =>
        {
            return true;
        }; // Skip SSL certificate validation

        // 2 Prepare request
        IRestRequest request = new RestRequest("/executor/python/", Method.POST);
        request.AddHeader("Authorization", "Bearer " + token);
        JsonObject jsonBody = new JsonObject();
        jsonBody.Add("script_name", scriptName.ToString());
        jsonBody.Add("wait_flag", waitFlag.IsTrue);
        if (!parameters.IsNull)
        {
            jsonBody.Add("parameters", parameters.ToString());
        }
        request.AddJsonBody(jsonBody);
        
        // 3 Execute
        IRestClient client = new RestClient(baseUrl);
        client.Timeout = 10 * 60 * 1000; // 10 minutes
        var response = client.Execute(request);
        if (!response.IsSuccessful)
        {
            throw new Exception(response.Content);
        }
    }
}