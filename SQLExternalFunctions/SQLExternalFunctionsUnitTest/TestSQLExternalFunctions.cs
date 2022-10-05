using System;
using System.Data.SqlTypes;
using NUnit.Framework;

namespace SQLExternalFunctionsUnitTest
{
    [TestFixture]
    public class Tests
    {

        [Test]
        public void TestExecutePython()
        {
            Console.WriteLine("Waiting 1 second");
            SQLExternalFunctions.ExecutePython("testScript.py", true, "-s=1");

            Console.WriteLine("Return 1");
            bool failed = false;
            try
            {
                SQLExternalFunctions.ExecutePython("testScript.py", true, "-r=1");
            }
            catch
            {
                failed = true;
            }

            Assert.IsTrue(failed);
            
            Console.WriteLine("Finished");
        }
    }
}